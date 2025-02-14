#!/usr/bin/env python3

import json
import logging
import argparse

from pandora.default import get_homedir, ConfigError

logger = logging.getLogger('Config validator')


def validate_generic_config_file():
    sample_config = get_homedir() / 'config' / 'generic.json.sample'
    with sample_config.open() as f:
        generic_config_sample = json.load(f)
    # Check documentation
    for key in generic_config_sample.keys():
        if key == '_notes':
            continue
        if key not in generic_config_sample['_notes']:
            raise ConfigError(f'###### - Documentation missing for {key}')

    user_config = get_homedir() / 'config' / 'generic.json'
    if not user_config.exists():
        # The config file was never created, copy the sample.
        with user_config.open('w') as _fw:
            json.dump(generic_config_sample, _fw)

    with user_config.open() as f:
        generic_config = json.load(f)

    # Check all entries in the sample files are in the user file, and they have the same type
    for key in generic_config_sample.keys():
        if key == '_notes':
            continue
        if generic_config.get(key) is None:
            logger.warning(f'Entry missing in user config file: {key}. Will default to: {generic_config_sample[key]}')
            continue
        if not isinstance(generic_config[key], type(generic_config_sample[key])):
            raise ConfigError(f'Invalid type for {key}. Got: {type(generic_config[key])} ({generic_config[key]}), expected: {type(generic_config_sample[key])} ({generic_config_sample[key]})')

        if isinstance(generic_config[key], dict):
            # Check entries
            for sub_key in generic_config_sample[key].keys():
                if sub_key not in generic_config[key]:
                    raise ConfigError(f'{sub_key} is missing in {generic_config[key]}. This is probably a new key, please update your config file accordingly. Default from sample file: {generic_config_sample[key][sub_key]}.')
                if not isinstance(generic_config[key][sub_key], type(generic_config_sample[key][sub_key])):
                    raise ConfigError(f'Invalid type for {sub_key} in {key}. Got: {type(generic_config[key][sub_key])} ({generic_config[key][sub_key]}), expected: {type(generic_config_sample[key][sub_key])} ({generic_config_sample[key][sub_key]})')

    # Make sure the user config file doesn't have entries missing in the sample config
    for key in generic_config.keys():
        if key not in generic_config_sample:
            raise ConfigError(f'{key} is missing in the sample config file. You need to compare {user_config} with {sample_config}.')

    return True


def update_user_configs():
    for file_name in ['generic']:
        with (get_homedir() / 'config' / f'{file_name}.json').open() as f:
            try:
                generic_config = json.load(f)
            except Exception:
                generic_config = {}
        with (get_homedir() / 'config' / f'{file_name}.json.sample').open() as f:
            generic_config_sample = json.load(f)

        has_new_entry = False
        for key in generic_config_sample.keys():
            if key == '_notes':
                continue
            if generic_config.get(key) is None:
                print(f'{key} was missing in {file_name}, adding it.')
                print(f"Description: {generic_config_sample['_notes'][key]}")
                generic_config[key] = generic_config_sample[key]
                has_new_entry = True
            elif isinstance(generic_config[key], dict):
                for sub_key in generic_config_sample[key].keys():
                    if sub_key not in generic_config[key]:
                        print(f'{sub_key} was missing in {key} from {file_name}, adding it.')
                        generic_config[key][sub_key] = generic_config_sample[key][sub_key]
                        has_new_entry = True
        if has_new_entry:
            with (get_homedir() / 'config' / f'{file_name}.json').open('w') as fw:
                json.dump(generic_config, fw, indent=2, sort_keys=True)
    return has_new_entry


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check the config files.')
    parser.add_argument('--check', default=False, action='store_true', help='Check if the sample config and the user config are in-line')
    parser.add_argument('--update', default=False, action='store_true', help='Update the user config with the entries from the sample config if entries are missing')
    args = parser.parse_args()

    if args.check:
        if validate_generic_config_file():
            print(f"The entries in {get_homedir() / 'config' / 'generic.json'} are valid.")

    if args.update:
        if not update_user_configs():
            print(f"No updates needed in {get_homedir() / 'config' / 'generic.json'}.")
