#!/usr/bin/env python3
import scapy.all as scapy
import geoip2.database
import requests
import tabulate
import json
import time
import logging
import socket
import sys

class NetPath:
    def __init__(self, dest, max_hops=30, timeout=2, probes=3):
        self.dest = dest
        self.max_hops = max_hops
        self.timeout = timeout
        self.probes = probes
        self.geoip = geoip2.database.Reader("GeoLite2-City.mmdb")
        self.results = []
        # Resolve destination hostname to IP
        try:
            self.dest_ip = socket.gethostbyname(dest)
            print(f"Resolved IP: {self.dest_ip}")
        except socket.gaierror:
            print("Could not resolve the hostname.")

    def get_as_info(self, ip):
        # Get AS number/org from ip-api.com
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            if data.get("status") == "success":
                return f"AS{data.get('as', 'Unknown')}"
            #return "Unknown"
        except Exception as e:
            print(f"Couldn't get AS info for {ip}: {e}")
            return "Unknown"

    def get_geo_info(self, ip):
        # Get city/country info for an IP
        try:
            response = self.geoip.city(ip)
            city = response.city.name or "Unknown"
            country = response.country.name or "Unknown"
            return f"{city}, {country}"
        except Exception as e:
            print(f"GeoIP lookup failed for {ip}: {e}")
            return "Unknown"

    def traceroute(self):
        print(f"Tracing route to {self.dest} ({self.dest_ip})")
        scapy.conf.iface = "en0"
        for ttl in range(1, self.max_hops + 1):
            hop = {"hop": ttl, "ip": None, "rtt": [], "loss": 0, "hostname": None, "geo": None, "as": None}
            replies = 0

            for _ in range(self.probes):
                pkt = scapy.IP(dst=self.dest, ttl=ttl) / scapy.ICMP()
                start = time.time()
                reply = scapy.sr1(pkt, timeout=self.timeout, verbose=0, iface="en0")
                rtt = (time.time() - start) * 1000
                if reply:
                    replies += 1
                    hop["ip"] = reply.src
                    hop["rtt"].append(round(rtt, 2))
                    try:
                        hop["hostname"] = socket.gethostbyaddr(reply.src)[0]
                    except socket.herror:
                        hop["hostname"] = "Unknown"

            hop["loss"] = round((1 - replies / self.probes) * 100, 2)
            if hop["ip"]:
                hop["geo"] = self.get_geo_info(hop["ip"])
                hop["as"] = self.get_as_info(hop["ip"])
            else:
                hop["ip"] = "*"
                hop["hostname"] = "N/A"
                hop["geo"] = "N/A"
                hop["as"] = "N/A"

            self.results.append(hop)

            # Stop if we hit the destination IP
            if hop["ip"] == self.dest_ip:
                break

        return self.results

    def show_results(self):
        table = []
        for hop in self.results:
            avg_rtt = round(sum(hop["rtt"]) / len(hop["rtt"]), 2) if hop["rtt"] else "N/A"
            rtt_list = ", ".join([str(rtt) for rtt in hop["rtt"]]) if hop["rtt"] else "N/A"
            table.append([
                hop["hop"],
                hop["ip"],
                hop["hostname"],
                rtt_list,
                avg_rtt,
                f"{hop['loss']}%",
                hop["geo"],
                hop["as"]
            ])
        headers = ["Hop", "IP", "Hostname", "RTTs (ms)", "Avg RTT (ms)", "Packet Loss", "Geo", "AS Info"]
        print(tabulate.tabulate(table, headers=headers, tablefmt="grid"))

    def save_to_json(self, filename="netpath_results.json"):
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=4)
        print(f"Saved results to {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dest = sys.argv[1]
    else:
        dest = input("Enter destination IP or hostname (e.g., 8.8.8.8): ") or "8.8.8.8"
    tracer = NetPath(dest)
    tracer.traceroute()
    tracer.show_results()
    tracer.save_to_json()
