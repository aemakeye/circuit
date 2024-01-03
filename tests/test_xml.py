import io
import json
import logging
from collections import ChainMap
from typing import List

import pytest
from circuit_analyser.diagram_api import DiagramApi
# from  import VALID_SHAPES_REGEXP
from circuit_analyser.diagram_elements import CElement, ElementFactory

logger = logging.getLogger(__name__)
TEST_DIAGRAM_FILE = 'tests/minimal_diagram.drawio'
TEST_DIAGRAM_FILE = 'tests/diagram_01.drawio'
TEST_DIAGRAM_FILE_JSON = 'tests/minimal_diagram.json'
TEST_DIAGRAM_FILE_JSON = TEST_DIAGRAM_FILE.replace("drawio","json")


def test_diagramapi_xml_to_dict_and_json_dump():
    dapi = DiagramApi()
    with open(TEST_DIAGRAM_FILE, 'r') as buf:
        # buf = io.StringIO(test_diagram)
        jd = dapi.create_diagram_from_xml(buf)
    with open(TEST_DIAGRAM_FILE_JSON, 'w') as j:
        j.write(json.dumps(jd.raw_dict, indent=4))
    # logger.info("%s" % json.dumps(jd.raw_dict, indent=4))
    # logger.debug("%s" % attrs.asdict(jd))
    assert jd.raw_dict.get('mxfile') is not None 
    assert jd.raw_dict['mxfile']['diagram']['mxGraphModel']['root']


def test_CElement_parse_nominal():
    tstr = "10"
    assert CElement.parse_nominal(tstr) == (10,0)
    tstr = "10 nano"
    assert CElement.parse_nominal(tstr) == (10,-9)
    tstr = "10 dfgbgdfbg fdgbv"
    assert CElement.parse_nominal(tstr) == (10,0)

@pytest.mark.parametrize("input_str, expected_class", [
    ('''
        {
        "@label": "",
        "@branch": "1",
        "@nominal": "10",
        "@id": "3",
        "mxCell": {
            "@style": "pointerEvents=1;verticalLabelPosition=bottom;shadow=0;dashed=0;align=center;html=1;verticalAlign=top;shape=mxgraph.electrical.resistors.resistor_1;comic=1;sketch=1;curveFitting=1;jiggle=2;",
            "@parent": "1",
            "@vertex": "1",
            "mxGeometry": {
                "@x": "510",
                "@y": "310",
                "@width": "100",
                "@height": "20",
                "@as": "geometry"
            }
        }
    }
    ''', "ResistorCreator"),
    ('''
        {
        "@label": "",
        "@branch": "7",
        "@id": "6",
        "mxCell": {
            "@style": "pointerEvents=1;verticalLabelPosition=bottom;shadow=0;dashed=0;align=center;html=1;verticalAlign=top;shape=mxgraph.electrical.inductors.inductor_3;sketch=1;curveFitting=1;jiggle=2;sketchStyle=comic;",
            "@parent": "1",
            "@vertex": "1",
            "mxGeometry": {
                "@x": "317",
                "@y": "410",
                "@width": "100",
                "@height": "8",
                "@as": "geometry"
            }
        }
        }''', "InductorCreator"),
        ('''
            {
                "@label": "",
                "@branch": "3",
                "@id": "7",
                "mxCell": {
                    "@style": "pointerEvents=1;verticalLabelPosition=bottom;shadow=0;dashed=0;align=center;html=1;verticalAlign=top;shape=mxgraph.electrical.signal_sources.source;aspect=fixed;points=[[0.5,0,0],[1,0.5,0],[0.5,1,0],[0,0.5,0]];elSignalType=dc1;",
                    "@vertex": "1",
                    "@parent": "1",
                    "mxGeometry": {
                        "@x": "590",
                        "@y": "460",
                        "@width": "60",
                        "@height": "60",
                        "@as": "geometry"
                    }
                }
            }
        ''', "SourceCreator"),
        ('''
            {
                "@label": "",
                "@branch": "2",
                "@id": "2",
                "mxCell": {
                    "@style": "shape=sumEllipse;perimeter=ellipsePerimeter;whiteSpace=wrap;html=1;backgroundOutline=1;sketch=1;curveFitting=1;jiggle=2;sketchStyle=comic;",
                    "@parent": "1",
                    "@vertex": "1",
                    "mxGeometry": {
                        "@x": "350",
                        "@y": "280",
                        "@width": "80",
                        "@height": "80",
                        "@as": "geometry"
                    }
                }
            }
        ''',"NodeCreator"),

])
def test_determine_creator(input_str, expected_class):
    DRTEST=json.loads(input_str)
    EF = ElementFactory()
    creator = EF.determine_creator(DRTEST)
    assert expected_class in  creator.__name__


def test_parse_circuit():
    with open(TEST_DIAGRAM_FILE_JSON, 'r') as tc:
        test_circuit = json.loads(tc.read())
        test_circuit = test_circuit.get("mxfile", {}).get("diagram", {}).get("mxGraphModel", {}).get("root", {}).get("object")
    EF = ElementFactory()
    
    assert type(test_circuit) == list
    elements = []
    for el in test_circuit:
        cel = None
        creator = EF.determine_creator(el)
        if creator:
            logger.info("current creator: %s" % creator.__name__)
            cel = creator.create(el)
            elements.append(cel)
        else:
            logger.info("skipping element with no creator")
    logger.info("Created elements: %s" % elements)



def test_diagram_init_from_xml():
    dapi = DiagramApi()
    with open(TEST_DIAGRAM_FILE, 'r') as df:
        dgrm = dapi.create_diagram_from_xml(df)
    
    # logger.info("Diagram Nodes: %s\n" % dgrm.nodes)
    # logger.info("Diagram elements: %s\n" % dgrm.elements)
    # logger.info("Diagram wires: %s\n" % dgrm.wires)
    assert "Diagram" in dgrm.__class__.__name__ 

def test_find_wire():
    dapi = DiagramApi()
    with open(TEST_DIAGRAM_FILE, 'r') as df:
        dgrm = dapi.create_diagram_from_xml(df)


    ID = 13
    # node = nodes[ID]
    logger.info(dgrm.wires)
    wires = [w for w in dgrm.wires if w.source == ID or w.target == ID]
    logger.info("adjusent %s wires: %s" % (len(wires), wires))
    # logger.info(dgrm.wires[14])
    # logger.info(json.dumps(dgrm.raw_dict, indent=4))

