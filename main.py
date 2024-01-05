import json

import requests

from helpers import CHAINS, get_subgraph_url


def get_stable_pools_with_rate_provider():
    """
    for every chain, query the official balancer subgraph and retrieve pools that:
    - have "stable" or "gyro" in their poolType
    - have a rate provider different from address(0)
    - have a liquidity greater than $300k
    - have a yield fee > 0
    """
    core_pools = {}
    for chain in CHAINS:
        core_pools[chain] = {}
        url = get_subgraph_url(chain)
        query = """{
            pools(
                first: 1000,
                where: {
                    and: [
                        {
                            priceRateProviders_: {
                                address_not: "0x0000000000000000000000000000000000000000"
                            }
                        },
                        {
                            or: [
                                {poolType_contains_nocase: "stable"},
                                {poolType_contains_nocase: "gyro"}
                            ]
                        },
                        {
                            totalLiquidity_gt: 300000
                        },
                        {
                            protocolYieldFeeCache_gt: 0
                        }
                    ]
                }
            ) {
                id,
                symbol
            }
        }"""
        r = requests.post(url, json={"query": query})
        r.raise_for_status()
        try:
            for pool in r.json()["data"]["pools"]:
                core_pools[chain][pool["id"]] = pool["symbol"]
        except KeyError:
            # no results for this chain
            pass
    return core_pools


if __name__ == "__main__":
    core_pools = get_stable_pools_with_rate_provider()

    # add pools from whitelist
    with open("config/whitelist.json", "r") as f:
        whitelist = json.load(f)
    for chain in whitelist:
        for pool, symbol in whitelist[chain].items():
            if pool not in core_pools[chain]:
                core_pools[chain][pool] = symbol

    # dump result to json
    json.dump(core_pools, open("out/core_pools.json", "w"), indent=2)
