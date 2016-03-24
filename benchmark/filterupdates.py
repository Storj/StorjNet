import os
import codecs
import json
import random
import time
import binascii
import argparse
import signal
from storjnet import quasar
from crochet import setup
from storjnet.api import start_swarm, stop_swarm
import logging
from twisted.python import log as _log


# STFU twisted
observer = _log.PythonLoggingObserver()
observer.start()
logging.basicConfig(level=60)


# start twisted via crochet and remove twisted handler
setup()
signal.signal(signal.SIGINT, signal.default_int_handler)


def warmup_dht(nodes):
    begin = time.time()
    while time.time() < (begin + 60.0 * 2.5):  # warmup for 2.5min
        node = random.choice(nodes)
        try:  # create random network walks
            node.dht_get(binascii.hexlify(os.urandom(32)))
        except:
            pass


def monkeypath_quasar(args):
    quasar._STATS_LOG = True
    quasar.SIZE = args['quasar_size']
    quasar.DEPTH = args['quasar_depth']
    quasar.TTL = args['quasar_ttl']
    quasar.FRESHNESS = args['quasar_freshness']
    quasar.REFRESH_TIME = args['quasar_refresh_time']
    quasar.EXTRA_PROPAGATIONS = args['quasar_extra_propagations']


def get_args():
    description = """Test filter updates."""
    parser = argparse.ArgumentParser(description=description)

    # TEST SETUP
    parser.add_argument(
        '--test_timedelta', type=float, default=1.0,
        help='Time between subscriptions.'
    )
    parser.add_argument(
        '--test_count', type=int, default=10,
        help='Number subscriptions.'
    )
    parser.add_argument(
        '--test_subscription_entropy', type=int, default=256,
        help='If subscriptions are all random or all to the same topic.'
    )

    # SWARM SETUP
    parser.add_argument(
        '--swarm_size', type=int, default=50,
        help='Size of the swarm.'
    )

    # QUASAR SETUP
    parser.add_argument(
        '--quasar_size', type=int,
        default=quasar.SIZE,
        help='Quasar filter size.'
    )
    parser.add_argument(
        '--quasar_depth', type=int,
        default=quasar.DEPTH,
        help='Quasar filter depth.'
    )
    parser.add_argument(
        '--quasar_ttl', type=int,
        default=quasar.DEPTH,
        help='Quasar event ttl.'
    )
    parser.add_argument(
        '--quasar_freshness', type=int,
        default=quasar.FRESHNESS,
        help='Time after unupdated peer filters become stale.')
    parser.add_argument(
        '--quasar_refresh_time', type=int,
        default=quasar.REFRESH_TIME,
        help='Interval when filters propagated.'
    )
    parser.add_argument(
        '--quasar_extra_propagations', type=int,
        default=quasar.EXTRA_PROPAGATIONS,
        help='Nr. of propagation allowed between refreshes.'
    )
    return vars(parser.parse_args())


def get_topic(entropy):
    assert(entropy <= 256)
    if entropy == 0:
        return str(0)
    i = int(codecs.encode(os.urandom(32), 'hex_codec'), 16)
    mask = 0
    for m in range(entropy):
        mask = mask + (1 << m)
    return str(i & mask)


def run_tests(nodes, args):
    timedelta = args["test_timedelta"]
    count = args["test_count"]
    for i in range(count):
        api, thread = random.choice(nodes)
        api.pubsub_subscribe(get_topic(args["test_subscription_entropy"]))
        time.sleep(timedelta)


def dump_results(args):
    data = {
        "quasar": quasar._STATS_DATA,
        "args": args
    }
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    args = get_args()
    monkeypath_quasar(args)
    nodes = start_swarm(size=args["swarm_size"], start_user_rpc_server=False)
    warmup_dht(nodes)
    try:
        run_tests(nodes, args)
    finally:
        stop_swarm(nodes)
        dump_results(args)
