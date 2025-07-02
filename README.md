# NetPath Project

NetPath is a Python-based network path analysis tool, designed to trace and visualize the route packets take from source to destination. It extends traditional traceroute by incorporating geolocation, ASN lookup, and support for ICMP, TCP, and UDP probes.

## Features

- Perform traceroute using ICMP, TCP (with multiple ports), and UDP
- Identify each router hop with:
  - IP address
  - Hostname (if resolvable)
  - Geographic location (City, Country)
  - ASN (Autonomous System Number)
- Detect routers that drop ICMP but respond to TCP/UDP
- Visualize hop-level statistics like RTT and packet loss
- Support for multiple probes per hop for accuracy
- Extendable architecture for further enhancements

## Requirements

- Python 3.6+
- Required Python Packages:
  - scapy
  - geoip2
  - requests
  - flask
  - tabulate

Install them using:
pip install -r requirements.txt

Additionally, download the GeoLite2-City.mmdb file from MaxMind:
https://dev.maxmind.com/geoip/geolite2/
Place the .mmdb file in the root directory of the project.

## Usage

1. Run the traceroute script:
   sudo python traceroute.py

3. React Web application:
   sudo python app.py

