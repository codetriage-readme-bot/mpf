""" Contains the base classes for drop targets and drop target banks."""
# drop_target.py
# Mission Pinball Framework
# Written by Brian Madden & Gabe Knuth
# Released under the MIT License. (See license info at the end of this file.)

# Documentation and more info at http://missionpinball.com/mpf

import logging

from mpf.system.devices import Device
from mpf.system.config import Config


class DropTarget(Device):
    """Represents a single drop target in a pinball machine.

    Args: Same as the `Target` parent class"""

    config_section = 'drop_targets'
    collection = 'drop_targets'
    class_label = 'drop_target'

    def __init__(self, machine, name, config, collection=None):
        self.log = logging.getLogger('DropTarget.' + name)
        self.device_str = 'droptarget'

        super(DropTarget, self).__init__(machine, name, config, collection)

        self.complete = False
        self.reset_coil = None
        self.knockdown_coil = None
        self.banks = set()

        config_spec = '''
                        switch: string
                        reset_coil: str|None
                        knockdown_coil: str|None

                        '''

        self.config = Config.process_config(config_spec, self.config)

        try:
            self.reset_coil = self.machine.coils[self.config['reset_coil']]
        except KeyError:
            pass

        try:
            self.knockdown_coil = self.machine.coils[self.config['knockdown_coil']]
        except KeyError:
            pass

        # can't read the switch until the switch controller is set up
        self.machine.events.add_handler('init_phase_3',
                                        self._update_state_from_switch)

    def _register_switch_handlers(self):
        # register for notification of switch state
        # this is in addition to the parent since drop targets track
        # self.complete in separately

        self.machine.switch_controller.add_switch_handler(self.config['switch'],
            self._update_state_from_switch, 0)
        self.machine.switch_controller.add_switch_handler(self.config['switch'],
            self._update_state_from_switch, 1)

    def knockdown(self, **kwargs):
        """Pulses the knockdown coil to knock down this drop target."""
        if self.knockdown_coil:
            self.knockdown_coil.pulse()

    def _update_state_from_switch(self):
        if self.machine.switch_controller.is_active(self.config['switch']):
            self._down()
        else:
            self._up()

    def _down(self):
        self.complete = True
        self.machine.events.post(self.name + '_down')

    def _up(self):
        self.complete = False
        self.machine.events.post(self.name + '_up')

    def _update_banks(self):

        for bank in self.banks:
            bank.update_member_target(self, self.complete)

    def add_to_bank(self, bank):
        """Adds this drop target to a drop target bank, which allows the bank to
        update its status based on state changes to this drop target.

        Args:
            bank: DropTargetBank object to add this drop target to.

        """
        self.banks.add(bank)

    def reset(self, **kwargs):
        """Resets this drop target.

        If this drop target is configured with a reset coil, then this method
        will pulse that coil. If not, then it checks to see if this drop target
        is part of a drop target bank, and if so, it calls the reset() method of
        the drop target bank.

        This method does not reset the target profile, however, the switch event
        handler should reset the target profile on its own when the drop target
        physically moves back to the up position.

        """

        if self.reset_coil:
            self.reset_coil.pulse()


class DropTargetBank(Device):
    """Represents a bank of drop targets in a pinball machine by grouping
    together multiple `DropTarget` class devices.

    """
    config_section = 'drop_target_banks'
    collection = 'drop_target_banks'
    class_label = 'drop_target_bank'

    def __init__(self, machine, name, config, collection=None):

        self.device_str = 'drop_targets'

        self.log = logging.getLogger('DropTargetBank.' + name)
        super(DropTargetBank, self).__init__(machine, name, config, collection)

        self.drop_targets = set()
        self.reset_coil = None
        self.reset_coils = set()
        self.complete = False
        self.down = 0
        self.up = 0

        if 'reset_coils' in self.config:
            for coil_name in Config.string_to_list(self.config['reset_coils']):
                self.reset_coils.add(self.machine.coils[coil_name])

        if 'reset_coil' in self.config:
            self.reset_coil = self.machine.coils[self.config['reset_coil']]

        self.config['drop_targets'] = (
            Config.string_to_list(config['drop_targets']))

        for target in self.config['drop_targets']:
            self.drop_targets.add(self.machine.drop_targets[target])
            self.machine.drop_targets[target].add_to_bank(self)

    def reset(self, **kwargs):
        """Resets this bank of drop targets.

        This method has some intelligence to figure out what coil(s) it should
        fire. It builds up a set by looking at its own reset_coil and
        reset_coils settings, and also scanning through all the member drop
        targets and collecting their coils. Then it pulses each of them. (This
        coil list is a "set" which means it only sends a single pulse to each
        coil, even if each drop target is configured with its own coil.)

        """
        # figure out all the coils we need to pulse
        coils = set()

        for drop_target in self.drop_targets:
            if drop_target.reset_coil:
                coils.add(drop_target.reset_coil)

        for coil in self.reset_coils:
            coils.add(coil)

        if self.reset_coil:
            coils.add(self.reset_coil)

        # now pulse them
        for coil in coils:
            coil.pulse()

    def member_target_change(self):
        """A member drop target has changed state.

        This method causes this group to update its down and up counts and
        complete status.

        """
        self.down = 0
        self.up = 0

        for target in self.drop_targets:
            if target.complete:
                self.down += 1
            else:
                self.up += 1

        if down == len(self.drop_targets):
            self._bank_down()
        if not down:
            self._bank_up()
        else:
            self._bank_mixed()

    def _bank_down(self):
        self.complete = True
        self.machine.events.post(self.name + '_down')

    def _bank_up(self):
        self.complete = False
        self.machine.events.post(self.name + '_up')

    def _bank_mixed(self):
        self.complete = False
        self.machine.events.post(self.name + '_mixed', down=self.down)

# The MIT License (MIT)

# Copyright (c) 2013-2015 Brian Madden and Gabe Knuth

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
