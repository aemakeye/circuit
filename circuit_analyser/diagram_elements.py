import logging
import re
from enum import IntEnum
from typing import Dict, List, Tuple
from xml.etree.ElementTree import Element

import attrs
from attrs import field

logger = logging.getLogger(__name__)
BRANCH_ATTRIBUTE_NAME = "branch"


class Units(IntEnum):
    nano = -9
    micro = -6
    milli = -3
    santi = -2
    deci = -1
    base = 0
    kilo = 3
    mega = 6


@attrs.define
class CElement:
    id: int # drawio id
    branch: int
    value: float
    units: str = ""
    g_id: int = -1
    multiplier: int = field(default=Units.base)

    @classmethod
    def parse_nominal(cls, nominal_value: str) -> Tuple[int, Units]:
        if not nominal_value:
            return (None, None)
        r = "(?P<value>\d+)\s*(?P<multiplier>\w+)?"
        m = re.match(r, nominal_value)
        md = m.groupdict()
        mult = md.get("multiplier", "base")
        if mult == None:  # TODO: wut?
            return (float(md.get("value")), 0)
        try:
            mult_v = Units[mult].value
        except KeyError:
            logger.error("Bad multiplier specification. %s is unknown" % mult)
            return (float(md.get("value")), Units["base"].value)

        return (float(md.get("value")), mult_v)

    @classmethod
    def from_xml_to_element(cls, subtree_as_dict: Dict):
        pass

    @classmethod
    def create(*args, **kwargs):
        raise NotImplemented


@attrs.define
class Resistor(CElement):
    units: str = "ohm"


@attrs.define
class Capacitor(CElement):
    units: str = "farada"


@attrs.define
class Inductor(CElement):
    units: str = "henry"


@attrs.define
class Node(CElement):
    units: str = "Volt"
    multiplier: int = 0
    value: float = None


@attrs.define
class Source(CElement):
    pass


@attrs.define
class Wire(CElement):
    value: float = None
    multiplier: int = 0
    source: int = None
    target: int = None


class MxCell(object):
    @classmethod
    def style_to_dict(cls, style: str):
        # deprecate
        sl = style.replace("=", ";").split(";")

        return dict(zip(sl[::2], sl[1::2]))


class ElementFactory:
    def __init__(self) -> None:
        self._ecreators = {
            "resistors": ResistorCreator,
            "capacitors": CapacityCreator,
            "inductors": InductorCreator,
            "sumEllipse": NodeCreator,
            "wire": WireCreator,
            "source": SourceCreator,
        }

    def register_etype_creator(self, etype, creator):
        self._ecreators[etype] = creator

    def get_ecreator(self, etype):
        ecreator = self._ecreators.get(etype)
        if not ecreator:
            return None
        return ecreator

    def determine_creator(self, d_object):
        eid = d_object.get("@id")
        if not eid:
            logger.error("No element id for object. Strange.\n%s" % d_object)
            return None
        # has_branch = d_object.get("@" + BRANCH_ATTRIBUTE_NAME)

        logger.info("determine creator for element with id %s" % eid)
        style_attr = d_object.get("mxCell", dict()).get("@style")
        if not style_attr:
            logger.error("no style attribute for element id %s" % eid)
            # raise AttributeError
            return None
        d_style_attr = MxCell.style_to_dict(style=style_attr)
        shape = d_style_attr.get("shape")
        if shape:
            if "sumEllipse" in shape:
                logger.info("Element with id %s is of type Node" % eid)
                return self.get_ecreator("sumEllipse")
            # if "resistors" in shape and has_branch:
            if "resistors" in shape:
                logger.info("Element with id %s is of type resistors" % eid)
                return self.get_ecreator("resistors")
            # if "inductors" in shape and has_branch:
            if "inductors" in shape:
                logger.info("Element with id %s is of type inductors" % eid)
                return self.get_ecreator("inductors")
            # if "capacitors" in shape and has_branch:
            if "capacitors" in shape:
                logger.info("Element with id %s is of type capacitor" % eid)
                return self.get_ecreator("capacitors")
            # if "signal_sources" in shape and has_branch:
            if "signal_sources" in shape:
                logger.info("Element with id %s is of type source" % eid)
                return self.get_ecreator("source")
            # to cases, when we get wires: arrow, and we append only when src and targets are set
            if (
                "connector" in shape
                and d_object.get("mxCell", dict()).get("@source")
                and d_object.get("mxCell", dict()).get("@target")
            ):
                logger.info("Element whith id %s is of type wire" % eid)
                return self.get_ecreator("wire")
        # or simple line, which we append if src and target are set
        elif d_object.get("mxCell", dict()).get("@source") and d_object.get(
            "mxCell", dict()
        ).get("@target"):
            return self.get_ecreator("wire")
        return None


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


class ResistorCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Resistor | None:
        id = int(ed.get("@id"))
        nominal = ed.get("@nominal")
        if not nominal:
            logger.error("Resistor %s without nominal" % id)
            raise ValueError
        nom = Resistor.parse_nominal(nominal)

        return Resistor(
            id=ed["@id"],
            branch=ed.get("@" + BRANCH_ATTRIBUTE_NAME),
            multiplier=nom[1],
            value=nom[0],
        )


class CapacityCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Capacitor | None:
        id = int(ed.get("@id"))
        nominal = ed.get("@nominal")
        if not nominal:
            logger.error("Capacitor %s without nominal" % id)
            raise ValueError
        nom = Capacitor.parse_nominal(nominal)
        return Capacitor(
            id=ed["@id"],
            branch=ed.get("@" + BRANCH_ATTRIBUTE_NAME),
            multiplier=nom[1],
            value=nom[0],
        )


class InductorCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Inductor | None:
        id = int(ed.get("@id"))
        nominal = ed.get("@nominal")
        if not nominal:
            logger.error("Inductor %s without nominal" % id)
            raise ValueError
        nom = Inductor.parse_nominal(nominal)

        return Inductor(
            id=id,
            branch=ed.get("@" + BRANCH_ATTRIBUTE_NAME),
            multiplier=nom[1],
            value=nom[0],
        )


class NodeCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Node | None:
        nom = Node.parse_nominal(ed.get("@nominal"))
        return Node(
            id=int(ed.get("@id")),
            branch=None,
            multiplier=nom[1],
            value=nom[0],
        )


class WireCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Wire | None:
        id=int(ed.get("@id"))
        source = int(ed.get("mxCell", dict()).get("@source"))
        target = int(ed.get("mxCell", dict()).get("@target"))

        return Wire(
            id=id,
            branch=ed.get("@" + BRANCH_ATTRIBUTE_NAME),
            source=source,
            target=target,
            value=None,
        )


class SourceCreator(Singleton):
    @classmethod
    def create(cls, ed: Dict) -> Source | None:
        id=int(ed.get("@id"))
        nom = Source.parse_nominal(ed.get("@nominal"))
        return Source(
            id=id,
            branch=ed.get("@" + BRANCH_ATTRIBUTE_NAME),
            multiplier=nom[1],
            value=nom[0],
        )
