from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


class Cell:
    tier: str
    start: int
    end: int
    value: str
    text: Optional[str]

    def get_previous(self, tier: List['Cell']) -> Optional['Cell']:
        idx = tier.index(self)
        try:
            return tier[idx - 1]
        except IndexError:
            return None

    def get_next(self, tier: List['Cell']) -> Optional['Cell']:
        idx = tier.index(self)
        try:
            return tier[idx + 1]
        except IndexError:
            return None

    def __init__(self, tier: str, start: int, end: int, value: str, text=None):
        self.tier = tier
        self.start = start
        self.end = end
        self.value = value
        self.text = text


class LD:
    start: int
    end: int

    referent: Cell
    direction: Cell
    np: Cell
    pronoun: Cell
    intervening: Cell

    previous_cu: Optional[str]
    cu: str
    next_cu: Optional[str]

    def __init__(self,
                 start: int, end: int,
                 referent: Cell, direction: Cell,
                 np: Cell, pronoun: Cell, intervening: Cell,
                 previous_cu: str, cu: str, next_cu: str):
        self.start = start
        self.end = end

        self.referent = referent
        self.direction = direction
        self.np = np
        self.pronoun = pronoun
        self.intervening = intervening

        self.previous_cu = previous_cu
        self.cu = cu
        self.next_cu = next_cu


class LDFile:
    path: Path
    narrative: str
    lds: List[LD]
    cu_count: int
    ld_count: int
    all_referents_count: int
    selected_referents_count: int

    def __init__(self, path: Path, narrative: str, lds: List[LD], cu_count: int, ld_count: int,
                 all_referents_count: int, selected_referents_count: int):
        self.path = path
        self.narrative = narrative
        self.lds = lds
        self.cu_count = cu_count
        self.ld_count = ld_count
        self.all_referents_count = all_referents_count
        self.selected_referents_count = selected_referents_count


def exb_in(directory: Path) -> [Path]:
    return [p for p in directory.glob('**/*.exb')]


def has_tier(soup: BeautifulSoup, tier: str) -> bool:
    return soup.find('tier', category=tier) is not None


def cells_in_tier(soup: BeautifulSoup, tier: str) -> List[Cell]:
    soup_tier = soup.find('tier', category=tier)
    soup_tier = list(soup_tier.children)
    cells: [Cell] = list()

    # Tier to cells
    for soup_cell in soup_tier:
        if isinstance(soup_cell, Tag):
            # 'T20' -> 20
            def cell_position_int(position: str) -> int:
                return int(position[1:])

            start = cell_position_int(soup_cell.attrs['start'])
            end = cell_position_int(soup_cell.attrs['end'])
            value = soup_cell.text

            cell = Cell(tier, start, end, value)
            cells.append(cell)

    return cells


def cells_within_cell(cell: Cell, search_tier: List[Cell]) -> List[Cell]:
    return [search_cell for search_cell in search_tier
            if search_cell.start >= cell.start
            and search_cell.end <= cell.end]


def cells_intersecting_with_cell(cell: Cell, search_tier: List[Cell]) -> List[Cell]:
    return [search_cell for search_cell in search_tier
            if cell.start <= search_cell.start <= cell.end
            or cell.start <= search_cell.end <= cell.end
            or search_cell.start <= cell.start <= search_cell.end
            or search_cell.start <= cell.end <= search_cell.end]


def cells_surrounding_cells(cell: Cell, search_tier: List[Cell]) -> List[Cell]:
    surrounding_cells = list()
    for search_cell in search_tier:
        if search_cell.start <= cell.start <= search_cell.end:
            surrounding_cells.append(search_cell)
            break
        if (cell.start <= search_cell.start
                and search_cell.end <= cell.end):
            surrounding_cells.append(search_cell)
            break
        if search_cell.start <= cell.end <= search_cell.end:
            surrounding_cells.append(search_cell)
            break
    return surrounding_cells
