import io
import logging
import xml.etree.ElementTree as ET
from collections import ChainMap
from dataclasses import field
from typing import Dict, List

import attrs
import xmltodict

from .diagram_elements import (CElement, ElementFactory, NodeCreator,
                               WireCreator)

logger = logging.getLogger(__name__)


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


@attrs.define
class Diagram(object):
    raw_xml: str
    raw_dict: Dict
    # items: Dict = attrs.field(init=False)
    elements: List = attrs.field(init=False)
    nodes: List = attrs.field(init=False)
    wires: List = attrs.field(init=False)
    _gen_eid: int = 0

    def id_generator(self):
        while True:
            self._gen_eid +=1
            yield self._gen_eid

    def __attrs_post_init__(self):
        self.elements = []
        self.nodes = []
        self.wires = []
        self._unmarshal_elements()
        # self.items = ChainMap(self.nodes, self.wires, self.elements)
        return

    def _unmarshal_elements(self):
        objects = (
            self.raw_dict.get("mxfile", {})
            .get("diagram", {})
            .get("mxGraphModel", {})
            .get("root", {})
            .get("object")
        )

        mxCells = (
            self.raw_dict.get("mxfile", {})
            .get("diagram", {})
            .get("mxGraphModel", {})
            .get("root", {})
            .get("mxCell")
        )

        DmxCells = [{ "@id": mc["@id"], "mxCell": mc} for mc in mxCells ]

        EF = ElementFactory()
        assert type(objects) == list
        for el in [*objects, *DmxCells]:
            cel = None
            creator = EF.determine_creator(el)
            if creator:
                logger.info("current creator: %s" % creator.__name__)
                cel = creator.create(el)
                if creator.__name__ == NodeCreator.__name__:
                    cel.g_id = next(self.id_generator())
                    self.nodes.append(cel)
                elif creator.__name__ == WireCreator.__name__:
                    self.wires.append(cel)
                else:
                    cel.g_id = next(self.id_generator())
                    self.elements.append(cel)
            else:
                logger.info(
                    "skipping element [id=%s] with no defined creator" % el.get("@id")
                )
        logger.info("unmarshaling elements complete")
        logger.debug("unmarshal result\n%s" % self.elements)

    def _combine_branches(self):
        pass


class DiagramApi(Singleton):
    @classmethod
    def xml_to_dict(cls, xml) -> Dict | None:
        try:
            d = xmltodict.parse(xml)
        except:
            logger.error("xmltodict failed")
            logger.debug("input data: %s" % xml)
            return None
        logger.debug(d)
        return d

    @classmethod
    def create_diagram_from_xml(cls, dio: io.TextIOWrapper) -> Diagram | None:
        rxml = dio.read()
        et = ET.fromstring(rxml)
        diagram = Diagram(raw_xml=et, raw_dict=DiagramApi.xml_to_dict(rxml))
        return diagram
