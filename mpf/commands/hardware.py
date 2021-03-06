"""Perform hardware operations."""
import os

from mpf.core.machine import MachineController

subcommand = True


class Command(object):

    """Performs hardware operations."""

    def __init__(self, mpf_path, machine_path, args):
        """Parse args."""
        self.mpf_path = mpf_path
        self.machine_path = machine_path
        self.args = args
        self.mpf = MachineController(self.mpf_path, self.machine_path,
                                     {"bcp": False,
                                      "no_load_cache": False,
                                      "mpfconfigfile": os.path.join(mpf_path, "mpfconfig.yaml"),
                                      "configfile": ["config"],
                                      "create_config_cache": False,
                                      "force_platform": False,
                                      "text_ui": False
                                      })
        self.mpf.initialise_mpf()

    def scan(self):
        """Scan hardware."""
        for name, platform in self.mpf.hardware_platforms.items():
            print("{}:".format(name))
            print(platform.get_info_string())
            print("---------")
