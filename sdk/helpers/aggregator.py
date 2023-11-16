import random

from config import SWAP_DEVIATION, ROUND_TO, NFT_MARKETPLACE_ALLOWANCE_AMOUNT
from constants import (
    STARKNET_DAI_TOKEN_ADDRESS,
    STARKNET_SWAP_TOKEN_PAIRS,
    STARKNET_ETH_TOKEN_ADDRESS
)
from sdk.database.data_item import DataItem
from sdk.models.dapp import Dapp
from sdk.models.event import Event


class Aggregator:
    def __init__(self, data_item: DataItem, token_in_for_swap: str, amount_in_for_swap: float):
        self.data_item = data_item
        self.suitable_dexes = Aggregator.get_suitable_dexes(data_item)
        self.suitable_nfts = Aggregator.get_suitable_nfts(data_item)
        self.nft_allowance_amount = random.uniform(*NFT_MARKETPLACE_ALLOWANCE_AMOUNT)
        self.token_in_for_swap = token_in_for_swap
        self.amount_in_for_swap = Aggregator.get_amount_in_for_swap(token_in_for_swap, amount_in_for_swap)
        self.dex_for_swap = Aggregator.get_dex_for_swap(self.suitable_dexes, token_in_for_swap)
        self.token_out_for_swap = Aggregator.get_token_out_for_swap(
            self.suitable_dexes,
            self.dex_for_swap,
            self.token_in_for_swap
        )

    def get_random_warmup_event(self):
        events = []

        if len(self.suitable_dexes) > 0:
            events.append(Event.SWAPS)
        if len(self.suitable_nfts) > 0:
            events.append(Event.NFTS)
        if self.data_item.dmail_tx_count > 0:
            events.append(Event.DMAIL)
        if self.data_item.zklend_deposit_tx_count > 0 or self.data_item.zklend_withdraw_tx_count > 0:
            events.append(Event.ZKLEND)

        random.shuffle(events)
        random_event = random.choice(events)

        return random_event

    @staticmethod
    def get_suitable_dexes(data_item: DataItem):
        suitable_dexes = []

        if data_item.myswap_swap_tx_count > 0:
            suitable_dexes.append(Dapp.MYSWAP)
        if data_item.jediswap_swap_tx_count > 0:
            suitable_dexes.append(Dapp.JEDISWAP)
        if data_item.tenkswap_swap_tx_count > 0:
            suitable_dexes.append(Dapp.TENKSWAP)
        if data_item.sithswap_swap_tx_count > 0:
            suitable_dexes.append(Dapp.SITHSWAP)
        if data_item.avnu_swap_tx_count > 0:
            suitable_dexes.append(Dapp.AVNU)

        return suitable_dexes

    @staticmethod
    def get_suitable_nfts(data_item: DataItem):
        suitable_nfts = []

        if data_item.nft_marketplace_allowance_tx_count > 0:
            suitable_nfts.append(Dapp.NFT_ALLOWANCE)
        if data_item.my_identity_mint_tx_count > 0:
            suitable_nfts.append(Dapp.MY_IDENTITY)
        if data_item.starkverse_mint_tx_count > 0:
            suitable_nfts.append(Dapp.STARKVERSE)

        return suitable_nfts

    @staticmethod
    def get_dex_for_swap(dexes: list, token_in: str):
        suitable_dexes_for_swap = []
        for dex in dexes:
            if dex == Dapp.SITHSWAP:
                if token_in == STARKNET_DAI_TOKEN_ADDRESS:
                    continue

            suitable_dexes_for_swap.append(dex.value)

        if len(suitable_dexes_for_swap) == 0:
            return Dapp.AVNU.value

        random.shuffle(suitable_dexes_for_swap)
        dex_for_swap = random.choice(suitable_dexes_for_swap)

        return dex_for_swap

    @staticmethod
    def get_token_out_for_swap(dexes: list, dex: Dapp, token_in: str):
        valid_pairs = Aggregator.filter_valid_pairs(token_in, STARKNET_SWAP_TOKEN_PAIRS)
        if not valid_pairs:
            raise ValueError("Token out for swap is None")

        if dex == Dapp.SITHSWAP and len(dexes) < 2:
            valid_pairs = Aggregator.remove_pairs_for_sithswap(valid_pairs)

        random.shuffle(valid_pairs)
        selected_pair = random.choice(valid_pairs)
        token_out_for_swap = next(token for token in selected_pair if token != token_in)

        return token_out_for_swap

    @staticmethod
    def filter_valid_pairs(token_in: str, pairs):
        return [pair for pair in pairs if token_in in pair]

    @staticmethod
    def remove_pairs_for_sithswap(pairs):
        return [pair for pair in pairs if STARKNET_DAI_TOKEN_ADDRESS not in pair]

    @staticmethod
    def get_amount_in_for_swap(token_in: str, amount_in: float):
        if token_in == STARKNET_ETH_TOKEN_ADDRESS:
            amount_in = round(amount_in * random.uniform(*SWAP_DEVIATION), ROUND_TO)
        else:
            amount_in = int(amount_in * 10 ** ROUND_TO) / 10 ** ROUND_TO

        return amount_in
