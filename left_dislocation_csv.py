# ================== LOOK HERE :) ==================
# If you're writing a .csv file, you'll want to `import csv`
import csv
import re
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from src import util
from src.util import LD, Cell, LDFile

INPUT_PATH = Path('..', 'input')
#INPUT_PATH = Path('..', 'all_exb')
EXB_FILES = sorted(util.exb_in(INPUT_PATH))

REFERENTS_WITH_LD = ['car1', 'man', 'woman2', 'driver1', 'car2',
                     'ball', 'couple', 'cars', 'drivers', 'woman1', 'family']


def create_ld(referent: Cell, intervening_tier: List[Cell], direction_tier: List[Cell],
              np_tier: List[Cell], pronoun_tier: List[Cell],
              cu_tier: List[Cell]) -> Optional[LD]:
    try:
        intervening = util.cells_intersecting_with_cell(referent, intervening_tier)[0]
        direction = util.cells_intersecting_with_cell(referent, direction_tier)[0]
        np = util.cells_intersecting_with_cell(referent, np_tier)[0]
        pronoun = util.cells_intersecting_with_cell(referent, pronoun_tier)[0]
    except IndexError:
        print('NOT ALL TIERS INTERSECT ================================')
        return None

    cu_cells = util.cells_surrounding_cells(referent, cu_tier)
    cu = ' '.join(cu.value for cu in cu_cells)
    previous_cu_cell = cu_cells[0].get_previous(cu_tier)
    previous_cu = previous_cu_cell.value if previous_cu_cell else None
    next_cu_cell = cu_cells[-1].get_next(cu_tier)
    next_cu = next_cu_cell.value if next_cu_cell else None

    return LD(referent.start, referent.end,
              referent, direction,
              np, pronoun, intervening,
              previous_cu, cu, next_cu)


class RefFile:

    path: str
    cu_count: int
    all_referents_count: int
    selected_referents_count: int

    def __init__(self, path, cu_count, all_referents_count, selected_referents_count):
        self.path = path
        self.cu_count = cu_count
        self.all_referents_count = all_referents_count
        self.selected_referents_count = selected_referents_count


def create_ref_file(path: Path, soup: BeautifulSoup):
    if not util.has_tier(soup, 'referent') and util.has_tier(soup, 'dipl'):
        return

    #cu_tier = util.cells_in_tier(soup, 'cu')
    all_referents_tier = util.cells_in_tier(soup, 'referent')

    selected_referents = [ref for ref in all_referents_tier
                          if ref.value in REFERENTS_WITH_LD]

    #cus_with_text = [cu for cu in cu_tier
    #                 if re.search(r"[a-zA-Z](?![^{(\[]*[})\]])", cu.value)]

    #cu_count = len(cus_with_text)
    cu_count = 0
    all_referents_count = len(all_referents_tier)
    selected_referents_count = len(selected_referents)

    return RefFile(path, cu_count, all_referents_count, selected_referents_count)


def create_ld_file(path: Path, soup: BeautifulSoup) -> Optional[LDFile]:
    if not (util.has_tier(soup, 'ld_intervening')
            and util.has_tier(soup, 'ld_referent')
            and util.has_tier(soup, 'ld_direction')
            and util.has_tier(soup, 'ld_np')
            and util.has_tier(soup, 'ld_pronoun')
            and util.has_tier(soup, 'cu')
            and util.has_tier(soup, 'dipl')):
        return

    intervening_tier = util.cells_in_tier(soup, 'ld_intervening')
    referent_tier = util.cells_in_tier(soup, 'ld_referent')
    direction_tier = util.cells_in_tier(soup, 'ld_direction')
    np_tier = util.cells_in_tier(soup, 'ld_np')
    pronoun_tier = util.cells_in_tier(soup, 'ld_pronoun')
    cu_tier = util.cells_in_tier(soup, 'cu')

    all_referents_tier = util.cells_in_tier(soup, 'referent')

    narrative_tier = util.cells_in_tier(soup, 'dipl')
    narrative = ' '.join([cell.value for cell in narrative_tier])

    # Add tier text
    for cell in np_tier:
        cell.text = ' '.join([c.value for c in util.cells_intersecting_with_cell(cell, narrative_tier)])
    for cell in direction_tier:
        cell.text = ' '.join([c.value for c in util.cells_intersecting_with_cell(cell, narrative_tier)])
    for cell in referent_tier:
        cell.text = ' '.join([c.value for c in util.cells_intersecting_with_cell(cell, narrative_tier)])
    for cell in pronoun_tier:
        cell.text = ' '.join([c.value for c in util.cells_intersecting_with_cell(cell, narrative_tier)])
    for cell in intervening_tier:
        cell.text = ' '.join([c.value for c in util.cells_intersecting_with_cell(cell, narrative_tier)])

    lds = [create_ld(referent_cell,
                     intervening_tier, direction_tier,
                     np_tier, pronoun_tier, cu_tier)
           for referent_cell in referent_tier]

    if not all(lds):
        print('NOT ALL LDS =============================')
        return None

    selected_referents = [ref for ref in all_referents_tier
                          if ref.value in REFERENTS_WITH_LD]

    cus_with_text = [cu for cu in cu_tier
                     if re.search(r"[a-zA-Z](?![^{(\[]*[})\]])", cu.value)]

    cu_count = len(cus_with_text)
    ld_count = len(lds)

    all_referents_count = len(all_referents_tier)
    selected_referents_count = len(selected_referents)

    return LDFile(path, narrative, lds, cu_count, ld_count, all_referents_count, selected_referents_count)



def write_ref_file_csv(ld_files: List[LDFile]):
    with open('../r/referent_counts.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['file_name', 'cu_count', 'all_referents_count', 'selected_referents_count']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ld_file in ld_files:
            fields = {'file_name': ld_file.path.name,
                      'cu_count': ld_file.cu_count,
                      'all_referents_count': ld_file.all_referents_count,
                      'selected_referents_count': ld_file.selected_referents_count}
            writer.writerow(fields)


# ============= LOOK HERE :) ==============
# This function writes the .csv file.
def write_ld_file_csv(ld_files: List[LDFile]):
    with open('../r/initial_output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['file_name',
                      'referent', 'direction', 'np', 'pronoun', 'intervening',
                      'ld_text', 'verb_phrase_text',
                      'np_text', 'pronoun_text', 'intervening_text',
                      'previous_cu', 'cu', 'next_cu', 'narrative',
                      'ld_count', 'cu_count', 'all_referents_count', 'selected_referents_count']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ld_file in ld_files:
            for ld in ld_file.lds:
                fields = {'file_name': ld_file.path.name,
                          'referent': ld.referent.value,
                          'direction': ld.direction.value,
                          'np': ld.np.value,
                          'pronoun': ld.pronoun.value,
                          'intervening': ld.intervening.value,
                          'ld_text': ld.referent.text,
                          'verb_phrase_text': ld.direction.text,
                          'np_text': ld.np.text,
                          'pronoun_text': ld.pronoun.text,
                          'intervening_text': ld.intervening.text,
                          'previous_cu': ld.previous_cu,
                          'cu': ld.cu,
                          'next_cu': ld.next_cu,
                          'narrative': ld_file.narrative,
                          'ld_count': ld_file.ld_count,
                          'cu_count': ld_file.cu_count,
                          'all_referents_count': ld_file.all_referents_count,
                          'selected_referents_count': ld_file.selected_referents_count}
                writer.writerow(fields)


if __name__ == '__main__':
    ld_files = list()
    for file_path in EXB_FILES:
        with file_path.open(encoding='utf-8') as file:
            # print(file_path.as_posix())
            file_soup = BeautifulSoup(file, features='html.parser')
            ld_file = create_ld_file(file_path, file_soup)
            #ld_file = create_ref_file(file_path, file_soup)
            if ld_file is not None:
                print(file_path.as_posix())
        ld_files.append(ld_file)
        #print(len(ld_files))

    #bad_files = [f.path for f in ld_files if f is None]
    #print('\n'.join(bad_files))

    ld_files = [f for f in ld_files if f is not None]
    write_ld_file_csv(ld_files)
    #write_ref_file_csv(ld_files)
