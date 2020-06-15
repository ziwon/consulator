# Consulator
Simple consul leader election with python

## Usage

```python
app_host = os.getenv('HOST', '0.0.0.0')
app_port = int(os.getenv('PORT', 8000))
app_id = shortuuid.ShortUUID().random(length=4)
app_tags = os.getenv('SERVICE_TAG', 'v1')
app_bind_interface = os.getenv('BIND_INTERFACE', 'eth0')

consulator = Consulator(consul_url, app_bind_interface)
consulator.register_service(
    service_name='echo',
    service_id=f'echo-{app_id}',
    service_port=app_port,
    service_tags=[app_tags]
)
consulator.create_session()
consulator.take_leader()
```

## Demo

```sh
$ make consul-up
$ make app-up
```

## Todo

- Update dynamically the DNS SRV record of a leader
