from typing import Optional, Sequence
from web3.exceptions import InsufficientData


def percentile(values: Optional[Sequence[int]]=None, percentile: Optional[
    float]=None) ->float:
    """Calculates a simplified weighted average percentile"""
    if values is None or percentile is None:
        raise InsufficientData("Both 'values' and 'percentile' must be provided")
    
    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")
    
    if not values:
        raise InsufficientData("The 'values' sequence cannot be empty")
    
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * percentile / 100
    
    if index.is_integer():
        return float(sorted_values[int(index)])
    else:
        lower_index = int(index)
        upper_index = lower_index + 1
        lower_value = sorted_values[lower_index]
        upper_value = sorted_values[upper_index]
        fraction = index - lower_index
        return lower_value + (upper_value - lower_value) * fraction
