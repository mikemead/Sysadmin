#!/usr/bin/env python
from subprocess import call
import xml.etree.ElementTree as ET
import os
import re
import shutil
import datetime

def _reboot_phone(exten):
        call('/usr/sbin/asterisk -rx "sip notify polycom-check-cfg ' + exten + '"', shell=True)

def _cfg_update(cfg_root, cfg):
        log_file = "cfg_update.log"
        logger = open(log_file, "a")

        exten = cfg[:4]

        # Let's backup the original config file
        src = cfg_root + "/" + cfg
        dst = cfg_root + "/" + cfg + ".bak"
        logger.write(str(datetime.datetime.now()) + ": Backing up " + src + " to " + dst + "\n")
        shutil.copyfile(src, dst)

        xmlcfg = ""
        # Load data from original config and sanitise
        for line in open(cfg_root + "/" + cfg):
                li = line.strip()
                if not li.startswith("#"):
                        xmlcfg += line.rstrip()
        xmlroot = ET.fromstring(xmlcfg)

        # Find XML element we want to update
        xmlelement = xmlroot.findall("./reg")

        # Change attributes as required
        for el in xmlelement:
                el.attrib["reg.1.auth.password"] = exten
                el.attrib["reg.1.server.1.address"] = "IPADDR"

        # Prepare and save over original
        xmltree = ET.ElementTree(xmlroot)
        logger.write(str(datetime.datetime.now()) + ": Updating " + src + "\n")
        xmltree.write(src)

        # Reboot phone
        logger.write(str(datetime.datetime.now()) + ": Rebooting phone at extension " + exten + "\n")
        _reboot_phone(exten)
        logger.close()

def main():
        cfg_root = "/tftpboot"
        cfg_rexp = re.compile('^[0-9]{4}.cfg$') # 4 digits + .cfg

        # First lets find all config files in the root that match our pattern
        for cfg in os.listdir(cfg_root):
                if cfg_rexp.match(cfg):
                        _cfg_update(cfg_root, cfg)

if __name__ == '__main__':
        main()