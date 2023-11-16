from typing import Union

from sdk.helpers.cryptography_manager import CryptographyManager, CryptographyMode


class DataItem:
    def __init__(
            self,
            starknet_private_key,
            starknet_wallet_salt,
            evm_private_key,
            proxy,
            withdrawal_address,
            dmail_tx_count,
            nft_marketplace_allowance_tx_count,
            myswap_swap_tx_count,
            jediswap_swap_tx_count,
            tenkswap_swap_tx_count,
            sithswap_swap_tx_count,
            avnu_swap_tx_count,
            my_identity_mint_tx_count,
            starkverse_mint_tx_count,
            zklend_deposit_tx_count,
            zklend_withdraw_tx_count,
            is_okx_withdraw_completed,
            is_bridge_completed,
            volume_amount,
            cryptography_mode: CryptographyMode = CryptographyMode.RAW
    ):
        self.starknet_private_key = DataItem.set_cryptography_value(starknet_private_key, cryptography_mode)
        self.starknet_wallet_salt = DataItem.set_cryptography_value(starknet_wallet_salt, cryptography_mode)
        self.evm_private_key = DataItem.set_cryptography_value(evm_private_key, cryptography_mode)
        self.proxy = DataItem.set_cryptography_value(proxy, cryptography_mode)
        self.withdrawal_address = withdrawal_address
        self.dmail_tx_count = dmail_tx_count
        self.nft_marketplace_allowance_tx_count = nft_marketplace_allowance_tx_count
        self.myswap_swap_tx_count = myswap_swap_tx_count
        self.jediswap_swap_tx_count = jediswap_swap_tx_count
        self.tenkswap_swap_tx_count = tenkswap_swap_tx_count
        self.sithswap_swap_tx_count = sithswap_swap_tx_count
        self.avnu_swap_tx_count = avnu_swap_tx_count
        self.my_identity_mint_tx_count = my_identity_mint_tx_count
        self.starkverse_mint_tx_count = starkverse_mint_tx_count
        self.zklend_deposit_tx_count = zklend_deposit_tx_count
        self.zklend_withdraw_tx_count = zklend_withdraw_tx_count
        self.is_okx_withdraw_completed = is_okx_withdraw_completed
        self.is_bridge_completed = is_bridge_completed
        self.volume_amount = volume_amount

    @staticmethod
    def set_cryptography_value(value: Union[str, int, bool], cryptography_mode: CryptographyMode):
        if cryptography_mode is CryptographyMode.ENCRYPT:
            return CryptographyManager.encrypt(value)

        if cryptography_mode is CryptographyMode.DECRYPT:
            return CryptographyManager.decrypt(value)

        return value
