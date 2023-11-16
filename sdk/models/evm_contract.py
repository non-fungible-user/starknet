from dataclasses import dataclass

from constants import (
    EVM_ORBITER_BRIDGE_CONTRACT_ADDRESS,
    EVM_STARKGATE_BRIDGE_CONTRACT_ADDRESS,
    EVM_ORBITER_ABI,
    EVM_STARKGATE_ABI
)
from sdk.helpers.utils import read_from_json


@dataclass
class Contract:
    address: str
    abi: dict


ORBITER_BRIDGE_CONTRACT = Contract(
    address=EVM_ORBITER_BRIDGE_CONTRACT_ADDRESS,
    abi=read_from_json(EVM_ORBITER_ABI)
)

STARKGATE_BRIDGE_CONTRACT = Contract(
    address=EVM_STARKGATE_BRIDGE_CONTRACT_ADDRESS,
    abi=read_from_json(EVM_STARKGATE_ABI)
)
