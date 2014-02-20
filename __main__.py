##
## REST Mock Framework
##
## Max Kuznetsov <max@ngti.nl> 2014
##

import sys

try:
   import argparse
except ImportError:
   import argparse_ext as argparse

import parser
import server

def error(msg):
    print msg

    sys.exit(1)

ap = argparse.ArgumentParser(description='REST Mock Framework')
ap.add_argument('-p',
                type=int,
                nargs=1,
                dest="port",
                default=[8000],
                help='TCP port to bind to')
ap.add_argument('-a',
                type=str,
                nargs=1,
                dest="address",
                default=[''],
                help='TCP address to bind to')
ap.add_argument('actions',
                type=str,
                nargs=1,
                metavar="/path/to/actions",
                help='Path to actions file')

args = ap.parse_args()

actions_path = args.actions[0]
port = args.port[0]
address = args.address[0]

try:
    actions = parser.parse_actions(actions_path)
except Exception as e:
    error("Unable to parse actions file: %s" % str(e))

while True:
    try:
        server.serve(actions, port=port, ip=address)
    except KeyboardInterrupt:
        break
    except Exception as e:
        error("Error in server loop: %s" % str(e))
