import asyncio

from modules.bridge import (
    batch_bridge_from_starknet,
    batch_bridge_from_evm,
    BridgeModes
)
from modules.collector import batch_collector
from modules.sender import batch_sender, batch_withdrawal_to_starknet
from modules.warmup import warmup, warmup_with_gas, warmup_low_bank
from sdk.database.database import Database
from sdk.helpers.logger import logger
from sdk.helpers.utils import greeting_message


async def main():
    try:
        greeting_message()
        module = input("Start module: ")

        if module == "1":
            Database.create_database()
        elif module == "2":
            await warmup()
        elif module == "3":
            await warmup_with_gas()
        elif module == "4":
            await warmup_low_bank()
        elif module == "5":
            await batch_collector()
        elif module == "6":
            await batch_sender()
        elif module == "7":
            await batch_withdrawal_to_starknet()
        elif module == "8":
            await batch_bridge_from_evm(BridgeModes.STARKGATE)
        elif module == "9":
            await batch_bridge_from_starknet(BridgeModes.STARKGATE)
        elif module == "10":
            await batch_bridge_from_starknet(BridgeModes.ORBITER)
        elif module == "11":
            await batch_bridge_from_evm(BridgeModes.ORBITER)
        elif module == "12":
            await batch_bridge_from_starknet(BridgeModes.LAYERSWAP)
        elif module == "13":
            await batch_bridge_from_evm(BridgeModes.LAYERSWAP)
        elif module == "14":
            pass
            # todo: await cairo_1_update(mode=BridgeModes.LAYERSWAP)
        else:
            logger.error(f"Invalid module number: {module}")

    except Exception as e:
        logger.error(str(e), send_to_tg=False)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
