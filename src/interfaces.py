from typing import List, TypedDict, Literal

class ISource(TypedDict):
    source_type: Literal['facebook_group']
    name: str
    username: str
    min_reaction: dict