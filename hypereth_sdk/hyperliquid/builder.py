"""
HyperLiquid builder fee information and related constants
"""


class HLBuilderInfo:
    """Contains HyperLiquid builder fee information and constants"""

    BUILDER_ADDRESS = "0x43539fA237e2F20Dbdb9A783bd8d8B5E99cEa4c9"
    BUILDER_FEE = 25  # 25bp

    @staticmethod
    def get_approve_builder_fee_data() -> dict:
        """
        Get the data needed for approving builder fee

        Returns:
            Dictionary with builder address and fee
        """
        return {
            "builder": HLBuilderInfo.BUILDER_ADDRESS,
            "fee": HLBuilderInfo.BUILDER_FEE
        }