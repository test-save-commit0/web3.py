import collections
import math
import operator
from typing import Iterable, Sequence, Tuple
from eth_typing import ChecksumAddress
from eth_utils import to_tuple
from eth_utils.toolz import curry, groupby, sliding_window
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.math import percentile
from web3.exceptions import InsufficientData, Web3ValidationError
from web3.types import BlockNumber, GasPriceStrategy, TxParams, Wei
MinerData = collections.namedtuple('MinerData', ['miner', 'num_blocks',
    'min_gas_price', 'low_percentile_gas_price'])
Probability = collections.namedtuple('Probability', ['gas_price', 'prob'])


@to_tuple
def _compute_probabilities(miner_data: Iterable[MinerData], wait_blocks:
    int, sample_size: int) ->Iterable[Probability]:
    """
    Computes the probabilities that a txn will be accepted at each of the gas
    prices accepted by the miners.
    """
    miner_data = sorted(miner_data, key=operator.attrgetter('min_gas_price'))
    for idx, data in enumerate(miner_data):
        num_blocks_accepting = sum(m.num_blocks for m in miner_data[idx:])
        probability = float(min(num_blocks_accepting, wait_blocks)) / float(sample_size)
        yield Probability(data.min_gas_price, probability)


def _compute_gas_price(probabilities: Sequence[Probability],
    desired_probability: float) ->Wei:
    """
    Given a sorted range of ``Probability`` named-tuples returns a gas price
    computed based on where the ``desired_probability`` would fall within the
    range.

    :param probabilities: An iterable of `Probability` named-tuples
        sorted in reverse order.
    :param desired_probability: An floating point representation of the desired
        probability. (e.g. ``85% -> 0.85``)
    """
    for left, right in sliding_window(2, probabilities):
        if desired_probability <= right.prob:
            return Wei(int(left.gas_price))
        elif right.prob < desired_probability < left.prob:
            prob_range = left.prob - right.prob
            price_range = left.gas_price - right.gas_price
            prob_delta = desired_probability - right.prob
            return Wei(int(right.gas_price + (prob_delta * price_range / prob_range)))
    return Wei(int(probabilities[-1].gas_price))


@curry
def construct_time_based_gas_price_strategy(max_wait_seconds: int,
    sample_size: int=120, probability: int=98, weighted: bool=False
    ) ->GasPriceStrategy:
    """
    A gas pricing strategy that uses recently mined block data to derive a gas
    price for which a transaction is likely to be mined within X seconds with
    probability P. If the weighted kwarg is True, more recent block
    times will be more heavily weighted.

    :param max_wait_seconds: The desired maximum number of seconds the
        transaction should take to mine.
    :param sample_size: The number of recent blocks to sample
    :param probability: An integer representation of the desired probability
        that the transaction will be mined within ``max_wait_seconds``.  0 means 0%
        and 100 means 100%.
    """
    def time_based_gas_price_strategy(web3: Web3, transaction_params: TxParams) -> Wei:
        if probability < 0 or probability > 100:
            raise Web3ValidationError(
                "The `probability` value must be a number between 0 and 100"
            )

        if sample_size < 2:
            raise Web3ValidationError(
                "The `sample_size` value must be at least 2"
            )

        latest_block = web3.eth.get_block('latest')
        latest_block_number = latest_block['number']

        max_wait_blocks = int(math.ceil(max_wait_seconds / 15))
        block_num = max(1, latest_block_number - sample_size)

        weighted_blocks = []
        for block_number in range(block_num, latest_block_number + 1):
            block = web3.eth.get_block(BlockNumber(block_number))
            if weighted:
                weight = (block_number - block_num + 1) / sample_size
            else:
                weight = 1

            weighted_blocks.append((block, weight))

        min_price = min(block['baseFeePerGas'] for block, _ in weighted_blocks)

        miner_data = groupby(
            operator.attrgetter('miner'),
            MinerData(
                block['miner'],
                weight,
                min_price,
                percentile(block['baseFeePerGas'], 10)
            ) for block, weight in weighted_blocks
        )

        miner_data = [
            MinerData(
                miner=miner,
                num_blocks=sum(m.num_blocks for m in data),
                min_gas_price=min(m.min_gas_price for m in data),
                low_percentile_gas_price=min(m.low_percentile_gas_price for m in data),
            )
            for miner, data
            in miner_data.items()
        ]

        raw_probabilities = _compute_probabilities(
            miner_data,
            wait_blocks=max_wait_blocks,
            sample_size=sample_size,
        )

        probabilities = tuple(sorted(
            raw_probabilities,
            key=operator.attrgetter('gas_price'),
            reverse=True,
        ))

        gas_price = _compute_gas_price(probabilities, probability / 100)

        return gas_price

    return time_based_gas_price_strategy


fast_gas_price_strategy = construct_time_based_gas_price_strategy(
    max_wait_seconds=60, sample_size=120)
medium_gas_price_strategy = construct_time_based_gas_price_strategy(
    max_wait_seconds=600, sample_size=120)
slow_gas_price_strategy = construct_time_based_gas_price_strategy(
    max_wait_seconds=60 * 60, sample_size=120)
glacial_gas_price_strategy = construct_time_based_gas_price_strategy(
    max_wait_seconds=24 * 60 * 60, sample_size=720)
