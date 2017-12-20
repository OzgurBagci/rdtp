"""This script is created because resolver is grew very big in the development process. This script ressolves the
interface that should be used while sending a package from an IP. This functions implemented as if it will be used
for general purpose."""

import socket
import json


def resolve_hostname(hostname):
    """This function resolves the interfaces that can be used and destination IPs by destinations' hostname."""

    my_name = socket.gethostname().partition('.')[0]   # Gets the hostname until the first dot

    # Routing table is read and converted to Python List.
    with open('../../resource/routing.json') as routing_table:
        routing_data = json.load(routing_table)

    my_data = [x for x in routing_data if list(x.keys())[0] == my_name][0][my_name]
    destination_ips = [x for x in my_data if list(x.keys())[0] == hostname][0][hostname]
    destination_routes = []
    for data in destination_ips:
        destination_routes.append({list(data.keys())[0]: list(data.values())[0]})

    final_destination_routes = {}
    resolve_helper(final_destination_routes, my_data, destination_routes)

    # Removes possible duplicates when multiple routes start from one route or opposite.
    for route in list(final_destination_routes.keys()):
        final_destination_routes[route] = list(set(final_destination_routes[route]))

    return final_destination_routes  # Returns a dictionary, key is the destination, value is the interface


def resolve_helper(final, my_data, destination_routes):
    """Loops until there is no reference from value to key which means value is the interface that will be used.
    It is a recursive function. Since this is a general purpose program every case is considered. Multiple interfaces
    may be connected to multiple routers for example."""

    for element in destination_routes:
        my_key = list(element.keys())[0]
        my_values = element[my_key]
        try:
            new_route = [x for x in my_data if list(x.keys())[0] == my_values][0][my_values]
            new_routes = []
            for data in new_route:
                new_routes.append({my_key: list(data.values())[0]})
            resolve_helper(final, my_data, new_routes)
        except (KeyError, IndexError):
            try:
                for route in list(destination_routes):
                    final[my_key].append(list(route.values())[0])
            except KeyError:
                for route in list(destination_routes):
                    final[my_key] = [list(route.values())[0]]
