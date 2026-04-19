import platform
import psutil
import wmi
import socket
import pythoncom

def get_cpu_info():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    cpu = c.Win32_Processor()[0]
    return {
        "name":      cpu.Name.strip(),
        "cores":     psutil.cpu_count(logical=False),
        "threads":   psutil.cpu_count(logical=True),
        "max_speed": f"{cpu.MaxClockSpeed} MHz",
        "usage":     psutil.cpu_percent(interval=1),
        "brand":     _detect_brand(cpu.Name, "cpu"),
    }

def get_ram_info():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    ram = psutil.virtual_memory()
    sticks = c.Win32_PhysicalMemory()
    stick_info = []
    for stick in sticks:
        stick_info.append({
            "capacity": f"{int(stick.Capacity) // (1024**3)} GB",
            "speed":    f"{stick.Speed} MHz",
            "type":     _get_ram_type(stick.SMBIOSMemoryType),
        })
    return {
        "total":   f"{ram.total // (1024**3)} GB",
        "used":    f"{ram.used // (1024**3)} GB",
        "free":    f"{ram.available // (1024**3)} GB",
        "percent": ram.percent,
        "sticks":  stick_info,
        "brand":   _detect_brand(sticks[0].Manufacturer if sticks else "", "ram"),
    }

def get_gpu_info():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    gpus = c.Win32_VideoController()
    result = []
    for gpu in gpus:
        vram = int(gpu.AdapterRAM or 0)
        result.append({
            "name":   gpu.Name.strip() if gpu.Name else "Unknown",
            "vram":   f"{vram // (1024**2)} MB" if vram > 0 else "N/A",
            "driver": gpu.DriverVersion or "N/A",
            "brand":  _detect_brand(gpu.Name or "", "gpu"),
        })
    return result

def get_motherboard_info():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    board = c.Win32_BaseBoard()[0]
    bios  = c.Win32_BIOS()[0]
    return {
        "manufacturer": board.Manufacturer.strip(),
        "model":        board.Product.strip(),
        "bios_version": bios.SMBIOSBIOSVersion.strip(),
        "bios_date":    bios.ReleaseDate[:8] if bios.ReleaseDate else "N/A",
        "brand":        _detect_brand(board.Manufacturer, "motherboard"),
    }

def get_disk_info():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    disks = c.Win32_DiskDrive()
    result = []
    for disk in disks:
        size = int(disk.Size or 0)
        result.append({
            "model": disk.Model.strip() if disk.Model else "Unknown",
            "size":  f"{size // (1024**3)} GB" if size > 0 else "N/A",
            "type":  "SSD" if "SSD" in (disk.Model or "") else "HDD",
            "brand": _detect_brand(disk.Model or "", "disk"),
        })
    return result

def get_os_info():
    return {
        "name":     platform.system(),
        "version":  platform.version(),
        "release":  platform.release(),
        "machine":  platform.machine(),
        "hostname": socket.gethostname(),
    }

def _detect_brand(name, category):
    name = name.lower()
    brands = {
        "intel":    ["intel"],
        "amd":      ["amd", "ryzen", "radeon"],
        "nvidia":   ["nvidia", "geforce", "rtx", "gtx"],
        "samsung":  ["samsung"],
        "kingston": ["kingston"],
        "corsair":  ["corsair"],
        "asus":     ["asus"],
        "gigabyte": ["gigabyte"],
        "msi":      ["msi"],
        "crucial":  ["crucial"],
        "seagate":  ["seagate"],
        "western":  ["western", "wd"],
        "toshiba":  ["toshiba"],
    }
    for brand, keywords in brands.items():
        if any(kw in name for kw in keywords):
            return brand
    return "default"

def _get_ram_type(smbios_type):
    types = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}
    return types.get(smbios_type, "Unknown")