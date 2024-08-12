from datetime import datetime
from os.path import basename, isdir
from os.path import join as path_join
from os.path import pardir
from shutil import make_archive

from lib.config import PatcherConfig
from lib.patch import load_patches


def patch(config_mod_path: str, config: PatcherConfig):
    #region Backup config_mod
    backup_path = path_join(
        config_mod_path,
        pardir,
        f'{basename(config_mod_path)}_{datetime.now().strftime('%Y-%m-%dT%H-%M')}'
    )
    if isdir(backup_path):
        make_archive(backup_path, 'zip', config_mod_path)
        print('Backup created successfully at: %s' % backup_path)
    #endregion Backup config_mod

    patchfiles = load_patches(config)

    patch_versions = list(sorted(patchfiles.keys()))
    min_version = config.patch_version + 1
    max_version = patch_versions[-1]
    assert patch_versions == list(range(max_version+1))

    for idx in range(min_version, max_version+1):
        print(f'> Patching with version {idx}...')
        patchfile = patchfiles[idx]

        for rel_config_path, patch in patchfile.items():
            config_path = path_join(config_mod_path, rel_config_path)
            patch.apply(config_path)
        print(f'> Patching version {idx} complete.')

    print('Patching complete')
    config.set_version(max_version)
    config.save()