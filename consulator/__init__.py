import time
import signal
import atexit
import socket
import consul
import netifaces

from loguru import logger
from six.moves.urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from consulator.utils import get_host_ip
from consulator.exception import *

TASK_WORKERS=2
DEFAULT_CHECK_INTERVAL='5s'
DEFAULT_SESSION_TTL=10 # 10s
DEFAULT_LOCK_DELAY=0.001
DEFAULT_SESSION_REFRESH_TIMEOUT=5.0

class Consulator(object):
    def __init__(self, consul_url, bind_interface, **kwargs):
        url = urlparse(consul_url)
        self._consul = consul.Consul(host=url.hostname, port=url.port or 80, **kwargs)
        self._bind_interface = bind_interface
        self._check_interval = kwargs.pop('check_interval', DEFAULT_CHECK_INTERVAL)
        self._session = None
        self._workers = ThreadPoolExecutor(max_workers=TASK_WORKERS)

        signal.signal(signal.SIGINT, self.deregister)
        atexit.register(self.deregister)
       
    def register_service(self, service_name, service_id, service_host=None, service_port=None, service_tags=[]):
        logger.debug(f"service_name: {service_name}, service_id: {service_id}, service_host: {service_host}, service_port: {service_port}")
        self._service_name = service_name
        self._service_id = service_id
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
                time.sleep(1)

    def refresh_session(self):
        logger.info("Refresh session")
        try:
            self._workers.submit(self._do_refresh_session)
        except (ConsulException):
            logger.exception("refresh_session")
        raise ConsulError("Failed to renew/create session")

    def update_leader(self):
        logger.info("Update leader")
        time.sleep(10)
        self._workers.submit(self.take_leader)

    def take_leader(self):
        while True:
            try:
                is_leader = self._consul.kv.put(
                    self._leader_path, 
                    self._service_id, 
                    acquire=self._session)
                logger.info(f"Leader: {is_leader}")
            except InvalidSession as e:
                logger.error(f"Could not take out TTL lock: {e}")
                self._sssion = None
            
            time.sleep(DEFAULT_SESSION_REFRESH_TIMEOUT)

    def _do_refresh_session(self):
        while True:
            if self._session:
                try:
                    logger.debug(f"Renew sessoin")
                    self._consul.session.renew(self._session)
                except consul.NotFound:
                    logger.debug(f"Session not found")
                    self._session = None

            if not self._session:
                try:
                    logger.debug(f"Create sessoin")
                    self._session = self._consul.session.create(
                        name=self._service_name, # distributed lock
                        ttl=DEFAULT_SESSION_TTL,
                        lock_delay=DEFAULT_LOCK_DELAY,
                        behavior="delete",
                    )
                    logger.info(f"Created sessoin: {self._session}")
                except InvalidSessionTTL:
                    logger.error(f"Session not created")

            time.sleep(DEFAULT_SESSION_REFRESH_TIMEOUT)

    def deregister(self):
        service = self._consul.agent.service
        service.deregister(self._service_id)
        logger.info('Deregister service: {}'.format(self._service_id))

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