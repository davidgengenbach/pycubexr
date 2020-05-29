from glob import glob

from pycubex_parser import CubexParser
from pycubex_parser.utils.exceptions import MissingMetricError


def main():
    for folder in sorted(glob('assets/*.r1')):
        print('-' * 99)
        print(folder)

        profile = f'{folder}/profile.cubex'

        with CubexParser(profile) as parsed:
            parsed.print_calltree()

            for metric in parsed.get_metrics():
                try:
                    metric_values = parsed.get_metric_values(metric=metric)
                    cnode = parsed.get_cnode(metric_values.cnode_indices[0])
                    cnode_values = metric_values.cnode_values(cnode.id)[:5]
                    region = parsed.get_region(cnode)
                    print('\t' + '-' * 100)
                    print(f'\tRegion: {region.name}\n\tMetric: {metric.name}\n\tMetricValues: {cnode_values})')
                except MissingMetricError as e:
                    # Ignore missing metrics
                    pass


if __name__ == '__main__':
    main()
