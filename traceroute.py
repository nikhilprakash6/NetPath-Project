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
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class NetPath:
    def __init__(self, dest, max_hops=30, timeout=3, probes=3, iface=None):
        self.dest = dest
        self.max_hops = max_hops
        self.timeout = timeout
        self.probes = probes
        self.iface = iface
        self.geoip = geoip2.database.Reader("GeoLite2-City.mmdb")
        self.results = []
        try:
            self.dest_ip = socket.gethostbyname(dest)
            logging.info(f"Resolved IP: {self.dest_ip}")
        except socket.gaierror:
            logging.error("Could not resolve the hostname.")
            sys.exit(1)

    def get_as_info(self, ip):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            if data.get("status") == "success":
                return data.get("as", "Unknown")
            return "Unknown"
        except Exception as e:
            logging.warning(f"Couldn't get AS info for {ip}: {e}")
            return "Unknown"

    def get_geo_info(self, ip):
        try:
            response = self.geoip.city(ip)
            city = response.city.name or "Unknown"
            country = response.country.name or "Unknown"
            return f"{city}, {country}"
        except Exception as e:
            logging.warning(f"GeoIP lookup failed for {ip}: {e}")
            return "Unknown"

    def traceroute(self):
        logging.info(f"Tracing route to {self.dest} ({self.dest_ip})")
        scapy.conf.iface = self.iface or scapy.conf.iface

        for ttl in range(1, self.max_hops + 1):
            logging.info(f"\n[TTL={ttl}] Probing...")
            hop = {
                "hop": ttl, "ip": None, "rtt": [], "loss": 100.0,
                "hostname": None, "geo": None, "as": None, "reply_proto": None
            }
            replies = []

            probe_types = [
                ("TCP:80", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.TCP(dport=80, flags="S")),
                ("TCP:443", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.TCP(dport=443, flags="S")),
                ("TCP:53", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.TCP(dport=53, flags="S")),
                ("TCP:22", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.TCP(dport=22, flags="S")),
                ("TCP:25", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.TCP(dport=25, flags="S")),
                ("ICMP", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.ICMP()),
                ("UDP:53", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.UDP(dport=53)),
                ("UDP:123", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.UDP(dport=123)),
                ("UDP:33434", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.UDP(dport=33434)),
                ("UDP:161", lambda: scapy.IP(dst=self.dest, ttl=ttl) / scapy.UDP(dport=161))
            ]

            destination_reached = False
            for probe_num in range(self.probes): # probe_num = 1, 2, 3
                if destination_reached:
                    break
                logging.info(f"  Probe #{probe_num + 1}:")
                for label, probe_func in probe_types:
                    if destination_reached:
                        break
                    try:
                        pkt = probe_func()
                        logging.debug(f"    Sending {label}...")
                        start = time.time()
                        reply = scapy.sr1(pkt, timeout=self.timeout, verbose=0, iface=self.iface)
                        rtt = (time.time() - start) * 1000

                        if reply:
                            # Handle ICMP Time Exceeded (intermediate hop) type = 11
                            if reply.haslayer(scapy.ICMP) and reply[scapy.ICMP].type == 11:
                                logging.info(f"    Reply from {reply.src} ({label}) in {round(rtt, 2)} ms")
                                replies.append(reply)
                                if not hop["ip"]:
                                    hop["ip"] = reply.src
                                    hop["reply_proto"] = label
                                    hop["rtt"].append(round(rtt, 2))
                                break
                            # Handle TCP SYN-ACK or RST (destination reached) SYN-ACK = 0x12, RST = 0x04
                            #elif reply.haslayer(scapy.TCP) and (reply[scapy.TCP].flags & 0x12 or reply[scapy.TCP].flags & 0x04):
                            elif reply.haslayer(scapy.TCP) and (reply[scapy.TCP].flags == 0x12 or reply[scapy.TCP].flags == 0x04):
                                logging.info(f"    Reply from {reply.src} ({label}) in {round(rtt, 2)} ms (Destination)")
                                replies.append(reply)
                                if not hop["ip"]:
                                    hop["ip"] = reply.src
                                    hop["reply_proto"] = label
                                    hop["rtt"].append(round(rtt, 2))
                                if reply.src == self.dest_ip:
                                    destination_reached = True
                                break
                            # Handle UDP Port Unreachable (destination reached) type = 0, code = 0 or type = 3, code = 3
                            elif reply.haslayer(scapy.ICMP) and ( reply[scapy.ICMP].type == 0 and reply[scapy.ICMP].code == 0 ) or ( reply[scapy.ICMP].type == 3 and reply[scapy.ICMP].code == 3 ):
                                logging.info(f"    Reply from {reply.src} ({label}) in {round(rtt, 2)} ms (Destination)")
                                replies.append(reply)
                                if not hop["ip"]:
                                    hop["ip"] = reply.src
                                    hop["reply_proto"] = label
                                    hop["rtt"].append(round(rtt, 2))
                                if reply.src == self.dest_ip:
                                    destination_reached = True
                                break
                            else:
                                logging.debug(f"    Unexpected reply for {label}: {reply.summary()}")
                        else:
                            logging.debug(f"    No reply for {label}")
                    except Exception as e:
                        logging.error(f"    Exception in probe {label}: {e}")
                        traceback.print_exc()

            if replies:
                hop["loss"] = round((1 - len(replies) / self.probes) * 100, 2)
                try:
                    hop["hostname"] = socket.gethostbyaddr(hop["ip"])[0]
                except socket.herror:
                    hop["hostname"] = "Unknown"
                hop["geo"] = self.get_geo_info(hop["ip"])
                hop["as"] = self.get_as_info(hop["ip"])
            else:
                hop["ip"] = "*"
                hop["hostname"] = "N/A"
                hop["geo"] = "N/A"
                hop["as"] = "N/A"
                hop["reply_proto"] = "None"
                logging.warning(f"No responses for TTL={ttl}. Possible missing hop.")

            self.results.append(hop)

            if destination_reached:
                logging.info(f"Destination {self.dest_ip} reached at hop {ttl}")
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
                hop["as"],
                hop["reply_proto"]
            ])
        headers = ["Hop", "IP", "Hostname", "RTTs (ms)", "Avg RTT (ms)", "Packet Loss", "Geo", "AS Info", "Reply Proto"]
        print(tabulate.tabulate(table, headers=headers, tablefmt="grid"))

    def save_to_json(self, filename="netpath_results.json"):
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=4)
        logging.info(f"Saved results to {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dest = sys.argv[1]
    else:
        dest = input("Enter destination IP or hostname (e.g., 8.8.8.8): ") or "8.8.8.8"
    tracer = NetPath(dest, timeout=3, probes=3)
    try:
        tracer.traceroute()
        tracer.show_results()
        tracer.save_to_json()
    except PermissionError:
        logging.error("Error: Run this script with root/admin privileges (e.g., sudo).")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Traceroute interrupted by user.")
        tracer.show_results()
        tracer.save_to_json()
