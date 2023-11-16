from decimal import Decimal
from typing import Union


class TokenAmount:
    wei: int
    ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.wei: int = amount
            self.ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.ether: Decimal = Decimal(str(amount))

        self.decimals = decimals
