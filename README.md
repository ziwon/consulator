# Consulator
Simple consul leader election with python

## Prerequisites

Assume that the following packages are already installed on your development system a virtual environment with Python3.

- [direnv](https://github.com/direnv/direnv)
- [pyenv](https://github.com/pyenv/pyenv)
- [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

## Quick Starts

```sh
$ git clone https://github.com/ziwon/consulator.git
$ cd consulator
direnv: loading .envrc
Reading .python-version...
direnv: using python 3.6.9
Reading .python-virtualenv...
direnv: export +VIRTUAL_ENV ~PATH

$ make app-build
$ make consul-up
$ make app-up
```

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
    # service_host=app_host `service_host` is automatically bind to the IP address of the given interface (ex. eth0)
    service_port=app_port,
    service_tags=[app_tags]
)
consulator.create_session()
consulator.take_leader()
```



## Todo

- ~Update dynamically the DNS SRV record of a leader~
- Unfortunately, it seems to have turned out that there's no way to update the DNS SRV record with Consul API/CLI.
