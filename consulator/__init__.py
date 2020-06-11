import socket
import consul
import time
from loguru import logger
from six.moves.urllib.parse import urlparse

from consulator.utils import get_host_ip
from consulator.exception import *

class Consulator(object):
    def __init__(self, consul_url, **kwargs):
        url = urlparse(consul_url)
        self._consul = consul.Consul(host=url.hostname, port=url.port, **kwargs)
        self._bind_interface = kwargs['bind_interface'] if 'bind_interface' in kwargs else "eth0"
        self._check_interval = kwargs['check_interval'] if 'check_interval' in kwargs else '5s' 
        self._session = None
        self.__session_checks = None
        
    def register_service(self, service_name, service_id, service_host=None, service_port=None, service_tags=[]):
        self._name = service_name
        service_host = service_host or get_host_ip(self._bind_interface)
        service = self._consul.agent.service
        check = consul.Check.tcp(service_host, service_port, self._check_interval)
        res = service.register(service_name, service_id, address=service_host, port=service_port, check=check, tags=service_tags)
        if res:
            logger.info(f'Register service: {service_name}({service_id})')
        else:
            logger.error(f'Register failed: {service_name}({service_id})')

    def create_session(self):
        while not self._session:
            try:
                logger.info("Trying to refresh session")
                self.refresh_session()
            except ConsulError:
                time.sleep(5)

    def refresh_session(self):
        try:
            self._do_refresh_session()
        except (ConsulException):
            logger.exception("refresh_session")
        raise ConsulError("Failed to renew/create session")

    def _do_refresh_session(self):
        if self._session and self._last_session_refresh + 5 > time.time():
            return False

        if self._session:
            try:
                self._consul.session.renew(self._session)
            except consul.NotFound:
                self._session = None

        if not self._session:
            try:
                self._session = self._consul.session.create(
                    name=self._name,
                    checks=self.__session_checks or [],
                    lock_delay=0.001,
                    behavior="delete",
                )
                logger.info(f"sessoin: {self._session}")
            except InvalidSessionTTL:
                logger.exception("session.create")
                #self.adjust_ttl()
                raise

        self._last_session_refresh = time.time()

    def adjust_ttl(self):
        try:
            settings = self._consul.agent.self()
            min_ttl = (
                settings["Config"]["SessionTTLMin"] or 10000000000
            ) / 1000000000.0
            logger.warning(
                "Changing Session TTL from %s to %s", self._consul.http.ttl, min_ttl
            )
            self._consul.http.set_ttl(min_ttl)
        except Exception:
            logger.exception("adjust_ttl")

    def deregister(self, service_id):
        service = self._consul.agent.service
        service.deregister(service_id)
        logger.info('Deregister service: {}'.format(service_id))

    def discovery_service(self, service_name):
        catalog = self._consul.catalog
        _, nodes =  catalog.service(service_name)
        services = []
        for node in nodes:
            services.append(node)
        return services

    def check_service(self, service_name):
        health = self._consul.health
        _, checks = health.checks(service_name)
        res = {}
        for check in checks:
            res[check['ServiceID']] = check
        return res

    def close(self):
        self._consul.close()