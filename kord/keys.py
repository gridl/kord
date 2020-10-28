from bestia.output import Row, FString, echo
from bestia.iterate import LoopedList

from .degrees import *
from .notes import *

class TonalKey(object):

    def __init__(self, chr, alt='', oct=0):
        self.root = Note(chr, alt, 0) # ignore note.oct

    def __repr__(self):
        spell_line = Row()
        for d in self.scale(
            note_count=len(self.root_intervals) +1, yield_all=False
        ):
            spell_line.append(
                FString(d, size=5)
            )
        return str(spell_line)

    def __getitem__(self, i):
        return self.degree(i)

    @property
    def name(self):
        return self.__class__.__name__

    @classmethod
    def __possible_root_notes(cls, valids=True):
        ''' checks all possible notes for validity as root of given key '''
        valid_roots = []
        invalid_roots = []

        for note in notes_by_alts():

            try:
                invalid_root = False
                for _ in cls(*note).scale(note_count=len(cls.root_intervals) +1, yield_all=0):
                    # if any degree fails, scale is not spellable
                    pass

            except InvalidNote:
                invalid_root = True

            finally:
                if invalid_root:
                    invalid_roots.append(note)
                else:
                    valid_roots.append(note)

        return valid_roots if valids else invalid_roots

    @classmethod
    def valid_root_notes(cls):
        ''' returns only valid root notes for given key class '''
        return cls.__possible_root_notes(valids=True)

    @classmethod
    def invalid_root_notes(cls):
        ''' returns only invalid root notes for given key class '''
        return cls.__possible_root_notes(valids=False)

    def degree_root_interval(self, d):
        ''' return degree's delta semitones from key's root '''
        if d > len(self.root_intervals):
            return self.degree_root_interval(
                d - len(self.root_intervals)
            ) + OCTAVE
        return self.root_intervals[d -1]


    def _spell(self, note_count=-1, start_note=None, yield_all=True, degree_order=[]):
        ''' 
            * returns when note_count == 0
            * positive note_count yields notes exactly
            * negative note_count yields notes indefinetly
            * filters Nones if needed
        '''
        for note in self._filter_degrees(
            start_note=start_note, degree_order=degree_order
        ):
            if note_count == 0:
                return

            if note:
                yield note
                note_count -= 1

            elif yield_all:
                yield None


    def _filter_degrees(self, start_note=None, degree_order=[]):
        ''' 
            * degree order is enforced for chords, modes, etc
        '''
        if not start_note:
            start_note = self.root

        if not degree_order:
            degree_order = [
                n+1 for n in range( len(self.root_intervals) )
            ]

        # calculate distance between octaves of first and last items of degree_order
        octave_delta = self.degree(degree_order[-1]).oct - self.degree(degree_order[0]).oct
        if not octave_delta:  # this cannot be 0 ...
            octave_delta = 1


        # yields only degree numbers
        i = 0

        while True:

            #   7 for Major, 12 for Chromatic
            o = len(self.root_intervals) * i

            for degree_index, _ in enumerate(degree_order):
                t = degree_order[degree_index]   + o  #  8 = 1 + 7*1
                p = degree_order[degree_index-1] + o  # 12 = 5 + 7*1
                if degree_index == 0:
                    p -= len(self.root_intervals) # should be 5

                this_degree = self.degree(t)
                prev_degree = self.degree(p)

                if this_degree < start_note:
                    continue

                # input([p, prev_degree, t, this_degree])

                # dont yield Nones before start_note
                if this_degree != start_note:
                    # yield non-diatonic semitones
                    last_interval = this_degree - prev_degree - 1
                    for st in range(last_interval):
                        yield None

                yield this_degree

            i += octave_delta

        input('DONE')
        return

        degs = LoopedList( * degs )

        # yields all degree numbers
        for note in self._solmizate(start_note=start_note):

            input(note)
            if note == None:
                yield None
                continue

            for deg in degs:
                # if note ** deg:
                if note >> deg:
                    yield note
                    break


    def _solmizate(self, start_note):
        '''
        * yields forever
        * always yields Nones
        * changes octs by calling degree()
        * start_note (diatonic, non-diatonic)
        '''
        d = 0
        while True:
            d += 1

            if self[d] < start_note:
                # start_note not yet reached
                continue

            # DONT YIELD EXTRA NONE BEFORE START_NOTE WHEN SCALE DEG BEFORE IS > 1 ST AWAY
            if self[d] != start_note:
                # yield non-diatonic semitones
                last_interval = self[d] - self[d -1] - 1
                for st in range(last_interval):
                    yield None

            yield self[d]


    def scale(self, note_count=0, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=range(1, len(self.root_intervals) +1),
        )


class DiatonicKey(TonalKey):

    def degree(self, d):

        if d < 1:
            return

        if d == 1:
            return self.root

        # GET DEGREE's ROOT OFFSETS = OCTAVE + SPARE_STS
        octs_from_root, spare_sts = divmod(
            self.degree_root_interval(d), OCTAVE
        )
        deg_oct = octs_from_root

        # GET DEGREE PROPERTIES FROM ENHARMONIC MATRIX
        next_degrees = [
            n for n in EnharmonicMatrix[
                self.root.enharmonic_row + spare_sts
            ] if n.chr == self.root.adjacent_chr(d -1) # EXPECTED TONE
        ]

        if len(next_degrees) == 1:
            deg = next_degrees[0]

            # AT THIS POINT DEG_OCT CAN EITHER STAY | +1
            if self.root.oversteps_oct(deg):
                deg_oct += 1

            # RETURN NEW OBJECT, DO NOT CHANGE ENHARMONIC MATRIX ITEM!
            return Note(deg.chr, deg.alt, deg_oct)

        raise InvalidNote


    def triad(self, note_count=3+1, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=(1, 3, 5),
        )

    def seventh(self, note_count=4+1, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=(1, 3, 5, 7),
        )

    def ninth(self, note_count=5+1, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=(1, 3, 5, 7, 9),
        )

    def eleventh(self, note_count=6+1, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=(1, 3, 5, 7, 9, 11),
        )

    def thirteenth(self, note_count=7+1, start_note=None, yield_all=True):
        return self._spell(
            note_count=note_count, start_note=start_note,
            yield_all=yield_all, degree_order=(1, 3, 5, 7, 9, 11, 13),
        )


########################
### MAJOR KEYS/MODES ###
########################

class MajorKey(DiatonicKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MAJOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MAJOR_SIXTH,
        MAJOR_SEVENTH,
    )

class IonianMode(MajorKey):
    pass

class MixolydianMode(MajorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MAJOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MAJOR_SIXTH,
        MINOR_SEVENTH, # <<<
    )

class LydianMode(MajorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MAJOR_THIRD,
        AUGMENTED_FOURTH, # <<<
        PERFECT_FIFTH,
        MAJOR_SIXTH,
        MAJOR_SEVENTH,
    )


########################
### MINOR KEYS/MODES ###
########################

class MinorKey(DiatonicKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MINOR_SIXTH,
        MINOR_SEVENTH,
    )
    
class MinorPentatonicKey(MinorKey):

    root_intervals = (
        UNISON,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MINOR_SEVENTH,
    )

class Hokkaido(MinorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MINOR_SIXTH,
    )


class NaturalMinorKey(MinorKey):
    pass

class MelodicMinorKey(MinorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MAJOR_SIXTH, # <<<
        MAJOR_SEVENTH, # <<<
    )

class HarmonicMinorKey(MinorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MINOR_SIXTH,
        MAJOR_SEVENTH, # <<<
    )

class AeolianMode(MinorKey):
    pass

class DorianMode(MinorKey):

    root_intervals = (
        UNISON,
        MAJOR_SECOND,
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MAJOR_SIXTH, # <<<
        MINOR_SEVENTH,
    )

class PhrygianMode(MinorKey):

    root_intervals = (
        UNISON,
        MINOR_SECOND, # <<<
        MINOR_THIRD,
        PERFECT_FOURTH,
        PERFECT_FIFTH,
        MINOR_SIXTH,
        MINOR_SEVENTH,
    )


#####################
### CHROMATIC KEY ###
#####################

class ChromaticKey(TonalKey):

    root_intervals = (
        UNISON,
        MINOR_SECOND,
        MAJOR_SECOND,
        MINOR_THIRD,
        MAJOR_THIRD,
        PERFECT_FOURTH,
        AUGMENTED_FOURTH,
        PERFECT_FIFTH,
        MINOR_SIXTH,
        MAJOR_SIXTH,
        MINOR_SEVENTH,
        MAJOR_SEVENTH,
    )

    def degree(self, d):

        if d < 1:
            return

        if d == 1:
            return self.root

        # GET DEGREE's ROOT OFFSETS = OCTAVE + SPARE_STS
        octs_from_root, spare_sts = divmod(
            self.degree_root_interval(d), OCTAVE
        )
        deg_oct = octs_from_root

        # GET DEGREE PROPERTIES FROM ENHARMONIC MATRIX
        # DO I REALLY NEED THESE 3 CHECKS ?
        # MATCH ROOT_TONE
        next_degrees = [
            n for n in EnharmonicMatrix[
                self.root.enharmonic_row + spare_sts
            ] if n ** self.root
        ]

        if not next_degrees:
            # MATCH ROOT_ALT

            next_degrees = [
                n for n in EnharmonicMatrix[
                    self.root.enharmonic_row + spare_sts
                ] if n.alt == self.root.alt[:-1]
            ]

            if not next_degrees:
                # CHOOSE "#" or ""
                chosen_alt = '#' if self.root.alt == '' else self.root.alt
                next_degrees = [
                    n for n in EnharmonicMatrix[
                        self.root.enharmonic_row + spare_sts
                    ] if n.alt == chosen_alt
                ]

        if len(next_degrees) == 1:

            deg = next_degrees[0] # got from ENH_MATRIX

            # AT THIS POINT DEG_OCT CAN EITHER STAY | +1
            if self.root.oversteps_oct(deg):
                deg_oct += 1

            # RETURN NEW OBJECT, DO NOT CHANGE ENHARMONIC MATRIX ITEM!
            return Note(deg.chr, deg.alt, deg_oct)

        raise InvalidNote

TONAL_CLASSES = {

    'major': MajorKey,

    'minor': MinorKey,
    'natural_minor': NaturalMinorKey,
    'melodic_minor': MelodicMinorKey,
    'harmonic_minor': HarmonicMinorKey,

    'ionian': IonianMode,
    'lydian': LydianMode,
    'mixo': MixolydianMode,
    'aeolian': AeolianMode,
    'dorian': DorianMode,
    'phrygian': PhrygianMode,

    # 'hokkaido': Hokkaido,

    'chromatic': ChromaticKey,

}

# CHORDS = {
#     # TRIADS ########################
#     '': MajorTriadChord,
#     'M': MajorTriadChord,

#     'm': MinorTriadChord,

#     'a': AugmentedTriadChord,
    #  '+': AugmentedTriadChord,

#     'd': DiminishedTriadChord,
#     '-': DiminishedTriadChord,

#     # SEVENTH #######################
#     '7': DominantSeventhChord,
#     'dom7': DominantSeventhChord,

#     'M7': MajorSeventhChord,
#     'maj7': MajorSeventhChord,
#     '△7': MajorSeventhChord,

#     'm7': MinorSeventhChord,
#     'min7': MinorSeventhChord,
    
#     'D7': DiminishedSeventhChord,
#     'dim7': DiminishedSeventhChord,
#     '°7': DiminishedSeventhChord,

#     'd7': HalfDiminishedSeventhChord, # isnt this one usually used for diminished (instead of D7)?
#     'm7-5': HalfDiminishedSeventhChord,
#     '⦰7': HalfDiminishedSeventhChord,

# }
