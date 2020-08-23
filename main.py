from stem.control import Controller
from stem import process, Signal
from os import getenv, path
from random import randint
import subprocess
import asyncio
import jinja2


def start_tor(socks: int, socks_port: int, control_port: int, tor_http_tunnel_port: int):

    control_ports = []
    socks_ports = []
    tor_http_tunnel_ports = []

    num_of_socks = range(socks)
    for i in num_of_socks:
        control_ports.append(f"{control_port + i}")
        socks_ports.append(f"{socks_port + i}")
        tor_http_tunnel_ports.append(f"{tor_http_tunnel_port + i}")

    process.launch_tor_with_config(config={
        'HTTPTunnelPort': tor_http_tunnel_ports,
        'ControlPort': control_ports,
        'SocksPort': socks_ports,
        'DNSPort': '53',
        'DNSListenAddress': '127.0.0.1'
    })


def reset_socks(socks: int, control_port: int):
    port = randint(control_port, control_port + socks)
    with Controller.from_port(port=port) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def create_ha_conf(socks: int, tor_http_tunnel_port: int, haproxy_port: int) -> str:
    template_filename = "./haproxy.cfg.j2"
    rendered_filename = "haproxy.cfg"
    render_vars = {
        "socks": socks,
        "tor_http_tunnel_port": tor_http_tunnel_port,
        "haproxy_port": haproxy_port
    }

    script_path = path.dirname(path.abspath(__file__))
    template_file_path = path.join(script_path, template_filename)
    rendered_file_path = path.join(script_path, rendered_filename)

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(script_path), autoescape=True, trim_blocks=True)
    output_text = environment.get_template(template_filename).render(render_vars)

    with open(rendered_file_path, "w") as result_file:
        result_file.write(output_text)
    
    return rendered_file_path


async def run_ha(rendered_file_path):
    ha_process = subprocess.Popen(['/usr/sbin/haproxy', '-f', rendered_file_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = ha_process.communicate()

if __name__ == '__main__':

    number_of_socks: int = getenv("number_of_socks", 10)
    haproxy_port: int = getenv("haproxy_port", 5000)
    starting_socks_port: int = getenv("starting_socks_port", 6080)
    starting_control_port: int = getenv("starting_control_port", 7080)
    tor_http_tunnel_port: int = getenv("tor_http_tunnel_port", 8000)

    start_tor(
        socks=int(number_of_socks),
        socks_port=int(starting_socks_port),
        control_port=int(starting_control_port),
        tor_http_tunnel_port=int(tor_http_tunnel_port)
    )

    rendered_file_path = create_ha_conf(
        socks=int(number_of_socks),
        haproxy_port=int(haproxy_port),
        tor_http_tunnel_port=int(tor_http_tunnel_port)
    )

    asyncio.run(run_ha(rendered_file_path=rendered_file_path))
