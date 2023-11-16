import json

from sdk.helpers.logger import logger


class LayerswapDataItem:
    def __init__(
            self,
            amount: float,
            source: str,
            destination: str,
            source_address: str,
            destination_address: str,
            source_asset: str = "ETH",
            destination_asset: str = "ETH",
            refuel: bool = False
    ):
        self.amount = str(amount)
        self.source = source
        self.destination = destination
        self.source_asset = source_asset
        self.destination_asset = destination_asset
        self.source_address = source_address
        self.destination_address = destination_address
        self.refuel = refuel

    def to_json(self):
        try:
            return json.dumps(self, default=lambda o: o.__dict__)
        except Exception as e:
            logger.error(f"LayerSwapDataItem to json object error: {str(e)}")
