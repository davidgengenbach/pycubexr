import tarfile
from tarfile import TarFile
from typing import List, Dict
from xml.etree import ElementTree

from pycubexr.classes import Metric, MetricValues, Region, CNode, Location
from pycubexr.parsers.anchor_xml_parser import parse_anchor_xml, AnchorXMLParseResult
from pycubexr.parsers.metrics_parser import extract_metric_values
from pycubexr.utils.exceptions import MissingMetricError


class CubexParser(object):
    _cubex_file: TarFile
    _cubex_filename: str
    _anchor_result: AnchorXMLParseResult
    _metric_values: Dict[int, MetricValues]

    def __init__(self, cubex_filename: str):
        self._cubex_filename = cubex_filename
        self._metric_values = {}

    def __enter__(self):
        self._cubex_file = tarfile.open(self._cubex_filename)

        with self._cubex_file.extractfile('anchor.xml') as anchor_file:
            anchor = ElementTree.parse(anchor_file)
            self._anchor_result = parse_anchor_xml(anchor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cubex_file.close()

    def get_metric_values(
            self,
            metric: Metric
    ) -> MetricValues:
        if metric.id in self._metric_values:
            return self._metric_values[metric.id]

        index_file_name = '{}.index'.format(metric.id)
        data_file_name = '{}.data'.format(metric.id)

        if index_file_name not in self._tar_file_members():
            raise MissingMetricError(metric)

        with self._cubex_file.extractfile(index_file_name) as index_file, \
                self._cubex_file.extractfile(data_file_name) as data_file:
            metric_values = extract_metric_values(
                metric=metric,
                index_file=index_file,
                data_file=data_file
            )

            assert metric_values.num_locations() == len(self.get_locations())

            self._metric_values[metric.id] = metric_values
            return metric_values

    def get_metrics(self):
        return self._anchor_result.metrics

    def get_metric_by_name(self, metric_name: str) -> Metric:
        return [metric for metric in self._anchor_result.metrics if metric.name == metric_name][0]

    def get_region(self, cnode: CNode) -> Region:
        return [region for region in self._anchor_result.regions if region.id == cnode.callee_region_id][0]

    def get_cnode(self, cnode_id: int) -> CNode:
        return [cnode for cnode in self._anchor_result.cnodes[0].get_all_children() if cnode.id == cnode_id][0]

    def get_region_by_name(self, name: str):
        return [region for region in self._anchor_result.regions if region.name == name][0]

    def all_cnodes(self):
        # TODO: is this always true?
        assert len(self._anchor_result.cnodes) == 1
        return self._anchor_result.cnodes[0].get_all_children()

    def get_cnodes_for_region(self, region_id: int):
        return [cnode for cnode in self.all_cnodes() if cnode.callee_region_id == region_id]

    def get_locations(self) -> List[Location]:
        return self._anchor_result.system_tree_nodes[0].all_locations()

    def get_calltree(self, indent=0, cnode: CNode = None):
        if cnode is None:
            cnode = self._anchor_result.cnodes[0]
        call_tree_string = ""
        child_string = ""
        child_string += "-" * indent + self.get_region(cnode).name
        call_tree_string += child_string
        call_tree_string += "\n"

        for child in cnode.get_children():
            tmp = self.get_calltree(indent + 1, cnode=child)
            if tmp is not None:
                call_tree_string += tmp

        return call_tree_string

    def print_calltree(self, indent=0, cnode: CNode = None):
        if cnode is None:
            cnode = self._anchor_result.cnodes[0]

        print('\t' * indent, self.get_region(cnode).name)

        for child in cnode.get_children():
            self.print_calltree(indent + 1, cnode=child)

    def _tar_file_members(self) -> List[str]:
        return [x.name for x in self._cubex_file.getmembers()]
