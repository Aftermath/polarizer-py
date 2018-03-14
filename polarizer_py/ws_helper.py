from typing import Mapping
from uuid import uuid4
from pathlib import Path
import asyncio
import websockets
import json
from pprint import pprint


def makeXUnitImportRequest(xunit: str, xargs: str = None):
    """
    Creates a WebSocket request to the Polarizer UMB verticle to do a Polarion /import/xunit import

    :param xunit: Path to the xunit xml file to submit
    :param xargs: Path to the json args file needed by polarizer
    :return:
    """
    op = "xunit-import-ws"
    tag = "xunit-import-{}".format(uuid4())
    ack = True
    data = {}
    with open(xunit, "r") as file:
        data["xunit"] = file.read()

    if xargs is None:
        # Look in default location
        home = Path.home()
        xargs = str(home)

    with open(xargs, "r") as file:
        data["xargs"] = file.read()

    data = json.dumps(data)

    return makeUMBRequest(op, tag=tag, ack=ack, data=data)


def makeTestCaseImportRequest(testcase: str, mapping: str, tcargs: str = None):
    """
    Creates a WebSocket request  to the Polarizer UMB verticle to do a Polarion /import/testcase import

    :param testcase: path to the TestCase xml that will be imported to Polarion
    :param mapping: path to the mapping.json file
    :param tcargs:
    :return: a websocket JSON with an updated mapping.json file
    """
    op = "testcase-import-ws"
    tag = "testcase-import-{}".format(uuid4())
    ack = True
    data = {}

    with open(mapping, "r") as mapfile:
        body = mapfile.read()
        data["mapping"] = body

    with open(testcase, "r") as tcfile:
        data["testcase"] = tcfile.read()

    if tcargs is None:
        # Look in default location
        home = Path.home()
        tcargs = str(home)

    with open(tcargs, "r") as argfile:
        data["tcargs"] = argfile.read()

    data = json.dumps(data)

    return makeUMBRequest(op, tag=tag, ack=ack, data=data)


def makeUMBRequest(op: str,
                   _type: str= "na",
                   tag=None,
                   ack: bool = False,
                   data: Mapping[str, str] = None):
    """
    Creates a python dict representing the JSON object to be sent over the websocket

    :param op:
    :param _type:
    :param tag:
    :param ack:
    :param data:
    :return:
    """
    if data is None:
        data = {}
    if tag is None:
        tag = uuid4()

    return {
        "op": op,
        "type": _type,
        "tag": tag,
        "ack": ack,
        "data": data
    }


async def serve(url: str = "/ws/xunit/import",
                args_path: str=None,
                xml_path: str=""):
    wsurl = "ws://localhost:9000{}".format(url)
    # req = makeXUnitImportRequest(xml_path, xargs=args_path)
    tp = '/home/stoner/Projects/testpolarize/'
    tcpath = tp + 'testcases/PLATTP/com.github.redhatqe.rhsm.testpolarize.TestReq/testUpgrade.xml'
    mapping = tp + 'mapping.json'
    tcargs = '/home/stoner/test-polarizer-testcase.json'

    req = makeTestCaseImportRequest(tcpath, mapping, tcargs=tcargs)

    print(req)
    print("=======================")
    print(req["data"])

    async with websockets.connect(wsurl) as websocket:
        body = json.dumps(req)
        await websocket.send(body)

        count = 0
        while count < 15:
            if count % 5 == 0:
                print("Waited {} seconds".format(count * 2))
            else:
                print("Count is now {}".format(count))
            try:
                # Have to use wait_for() here, otherwise websocket.recv will yield, effectively stopping the while loop
                # Yup, asyncio is tricky :)  Also, in python 3.5 can't use yield from in an async function
                response = await asyncio.wait_for(websocket.recv(), 2)
                print("<", end='')
                pprint(json.loads(response), indent=2, width=120)
            except asyncio.TimeoutError:
                count += 1


if __name__ == "__main__":
    xunit = "/home/stoner/Projects/testpolarize/test-output/testng-polarion.xml"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serve(url='/ws/testcase/import',
                                  xml_path=xunit, args_path="/home/stoner/test-polarizer-xunit.json"))