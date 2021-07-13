"""
Main tests for library
"""

import os
import time

import testinfra.utils.ansible_runner
from tests.ansible_utils import (
    get_consumer_group,
    get_topic_name,
    cg_defaut_configuration,
    topic_defaut_configuration,
    sasl_default_configuration,
    ensure_kafka_topic,
    check_unconsumed_topic,
    ensure_kafka_consumer_group,
    produce_and_consume_topic,
    ensure_idempotency
)

runner = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE'])
testinfra_hosts = runner.get_hosts('executors')

kafka_hosts = dict()
for host in testinfra.get_hosts(
    ['kafka1'],
    connection='ansible',
    ansible_inventory=os.environ['MOLECULE_INVENTORY_FILE']
):
    kafka_hosts[host] = host.ansible.get_variables()


def test_delete_consumer_offset(host):
    """
    Check if can update replication factor
    """
    # Given
    topic_name1 = get_topic_name()
    consumer_group = get_consumer_group()

    ensure_kafka_topic(
        host,
        topic_defaut_configuration,
        topic_name1
    )
    time.sleep(0.3)

    produce_and_consume_topic(topic_name1, 1, consumer_group, True)
    time.sleep(0.3)

    # When
    test_cg_configuration = cg_defaut_configuration.copy()

    test_cg_configuration.update({
        'consumer_group': consumer_group,
        'action': 'delete',
        'api_version': '2.4.0',
        'topics': [{
            'name': topic_name1,
            'partitions': [0]
        }]
    })

    test_cg_configuration.update(sasl_default_configuration)
    ensure_idempotency(
        ensure_kafka_consumer_group(
            host,
            test_cg_configuration
        )
    )
    time.sleep(0.3)
    # Then
    for host, host_vars in kafka_hosts.items():
        kfk_addr = "%s:9092" % \
            host_vars['ansible_eth0']['ipv4']['address']['__ansible_unsafe']
        check_unconsumed_topic(consumer_group, topic_name1, kfk_addr)
