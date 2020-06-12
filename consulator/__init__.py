import time
import socket
import consul
import netifaces

from loguru import logger
from six.moves.urllib.parse import urlparse

from consulator.utils import get_host_ip
from consulator.exception import *


SESSION_TTL=86400 # between 10 and 86400 seconds
LOCK_DELAY=0.001

class Consulator(object):
    def __init__(self, consul_url, bind_interface, **kwargs):
        url = urlparse(consul_url)
        self._consul = consul.Consul(host=url.hostname, port=url.port or 80, **kwargs)
        self._bind_interface = bind_interface
        self._check_interval = kwargs.pop('check_interval', '5s')
        self._session = None
        self._last_session_refresh = 0
        self.__session_checks = None
        
    def register_service(self, service_name, service_id, service_host=None, service_port=None, service_tags=[]):
        self._name = service_name
        self._leader_path = f"{service_name}/leader"
        logger.debug(f"bind_interface: {self._bind_interface}")
        service_host = service_host or get_host_ip(self._bind_interface)
        service = self._consul.agent.service
        check = consul.Check.tcp(service_host, service_port, self._check_interval)
        res = service.register(service_name, service_id, address=service_host, port=service_port, check=check, tags=service_tags)
        if res:
            logger.info(f'Registered service: {service_name}({service_id})')
        else:
            logger.error(f'Registering failed: {service_name}({service_id})')

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

    def take_leader(self):
        try:
            is_leader = self._consul.kv.put(self._leader_path, self._name, acquire=self._session)
            logger.info(f"Leader: {is_leader}")
        except InvalidSession as e:
            logger.error(f"Could not take out TTL lock: {e}")
            self._sssion = None

    def _do_refresh_session(self):
        if self._session and self._last_session_refresh + 5 > time.time():
            logger.debug(f"sessoin is None, time condition not matched")
            return False

        if self._session:
            try:
                logger.debug(f"renew sessoin")
                self._consul.session.renew(self._session)
            except consul.NotFound:
                self._session = None

        if not self._session:
            try:
                self._session = self._consul.session.create(
                    name=self._name, # distributed lock
                    ttl=SESSION_TTL,
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