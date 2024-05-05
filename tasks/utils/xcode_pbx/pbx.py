import os
import shutil
from typing import Dict, List
import json
import uuid
import re
import openstep_parser as osp


def remove_path(path):
    if os.path.exists(path):
        print("rmove path:" + path)
        shutil.rmtree(path, True)

_FILE_TYPES = {
    '': ('text', 'PBXResourcesBuildPhase', None),
    '.a': ('archive.ar', 'PBXFrameworksBuildPhase', None),
    '.app': ('wrapper.application', None, None),
    '.s': ('sourcecode.asm', 'PBXSourcesBuildPhase', None),
    '.c': ('sourcecode.c.c', 'PBXSourcesBuildPhase', None),
    '.cpp': ('sourcecode.cpp.cpp', 'PBXSourcesBuildPhase', None),
    '.framework': ('wrapper.framework', 'PBXFrameworksBuildPhase', None),
    '.h': ('sourcecode.c.h', 'PBXHeadersBuildPhase', None),
    '.hpp': ('sourcecode.c.h', 'PBXHeadersBuildPhase', None),
    '.pch': ('sourcecode.c.h', 'PBXHeadersBuildPhase', None),
    '.d': ('sourcecode.dtrace', 'PBXSourcesBuildPhase', None),
    '.def': ('text', 'PBXResourcesBuildPhase', None),
    '.swift': ('sourcecode.swift', 'PBXSourcesBuildPhase', None),
    '.icns': ('image.icns', 'PBXResourcesBuildPhase', None),
    '.m': ('sourcecode.c.objc', 'PBXSourcesBuildPhase', None),
    '.j': ('sourcecode.c.objc', 'PBXSourcesBuildPhase', None),
    '.mm': ('sourcecode.cpp.objcpp', 'PBXSourcesBuildPhase', 4),
    '.nib': ('wrapper.nib', 'PBXResourcesBuildPhase', None),
    '.plist': ('text.plist.xml', 'PBXResourcesBuildPhase', None),
    '.json': ('text.json', 'PBXResourcesBuildPhase', None),
    '.png': ('image.png', 'PBXResourcesBuildPhase', None),
    '.jpg': ('image.jpg', 'PBXResourcesBuildPhase', None),
    '.rtf': ('text.rtf', 'PBXResourcesBuildPhase', None),
    '.tiff': ('image.tiff', 'PBXResourcesBuildPhase', None),
    '.txt': ('text', 'PBXResourcesBuildPhase', None),
    '.xcodeproj': ('wrapper.pb-project', None, None),
    '.xib': ('file.xib', 'PBXResourcesBuildPhase', None),
    '.strings': ('text.plist.strings', 'PBXResourcesBuildPhase', None),
    '.bundle': ('wrapper.plug-in', 'PBXResourcesBuildPhase', None),
    '.dylib': ('compiled.mach-o.dylib', 'PBXFrameworksBuildPhase', None),
    '.xcdatamodeld': ('wrapper.xcdatamodel', 'PBXSourcesBuildPhase', None),
    '.xcassets': ('folder.assetcatalog', 'PBXResourcesBuildPhase', None),
    '.xcconfig': ('sourcecode.xcconfig', 'PBXSourcesBuildPhase', None),
    '.tbd': ('sourcecode.text-based-dylib-definition', 'PBXFrameworksBuildPhase', None),
    '.bin': ('archive.macbinary', 'PBXResourcesBuildPhase', None),
    '.mlmodel': ('file.mlmodel', 'PBXSourcesBuildPhase', None),
    '.html': ('text.html', 'PBXResourcesBuildPhase', None),
    '.lproj': ('text.plist.strings', None, None),
    '.entitlements': ('text.plist.entitlements', 'PBXResourcesBuildPhase', None)
}

_SPECIAL_FOLDERS = ['.bundle', '.framework', '.xcodeproj', '.xcassets', '.xcdatamodeld', '.storyboardc']
_VALID_KEY_REGEX = re.compile(r'^[a-zA-Z0-9\\._/]*$')
_ESCAPE_REPLACEMENTS = [
    ('\\', '\\\\'),
    ('\n', '\\n'),
    ('\"', '\\"'),
    ('\0', '\\0'),
    ('\t', '\\\t'),
    ('\'', '\\\''),
]


def _get_key(data, key):
    if key in data:
        return data[key]
    return None


#attribs=["Weak"]
def PBXGetSet(attribs: list):
    if attribs and len(attribs) > 0:
        return {"settings": attribs}
    return None


def _escape(item, exclude=None):
    if len(item) != 0 and _VALID_KEY_REGEX.match(item) is not None:
        return item

    escaped = item
    for unescaped_value, escaped_value in _ESCAPE_REPLACEMENTS:
        if unescaped_value in exclude:
            continue
        escaped = escaped.replace(unescaped_value, escaped_value)

    return '"' + escaped + '"'


# 转换数组为字符串
def _listToString(data, indent):
    text = "(\n"
    indent += "\t"
    for value in data:
        text += indent + _valueToString(value, indent) + ",\n"
    indent = indent[0:len(indent) - 1]
    text += indent + ")"
    return text


# 转换字典为字符串
def _dictToString(data, indent):
    text = "{\n"
    indent += "\t"
    for (k, v) in data.items():
        if re.match('([0-9A-F]{24})', k) is None:
            k = _escape(k.__str__(), exclude=['\''])
        text += f'{indent}{k} = {_valueToString(v, indent)};\n'
    indent = indent[0:len(indent) - 1]
    text += indent + "}"
    return text


    # 转换值为字符串
def _valueToString(value, indent):
    if value is None:
        return ""
    if isinstance(value, dict):
        return _dictToString(value, indent)
    if isinstance(value, list):
        return _listToString(value, indent)
    return _escape(value.__str__(), exclude=['\''])


#判断文件类型
def _determine_file_type(path):
    filename = os.path.split(path)[1]
    ext = os.path.splitext(filename)[1]
    if os.path.isdir(os.path.abspath(path)) and ext not in _SPECIAL_FOLDERS:
        return "folder", 'PBXResourcesBuildPhase'
    if ext not in _FILE_TYPES:
        raise Exception(f'文件类型未知:{path} ext:{ext} filename:{filename}')
        # return None, 'PBXResourcesBuildPhase'
    return _FILE_TYPES[ext]


#生成唯一id
def _generate_id():
    return ''.join(str(uuid.uuid4()).upper().split('-')[1:])


# 基础对象
class PBXObject:

    def __init__(self, object_id: str, data: dict):
        if object_id and object_id != "":
            self.object_id = object_id
        else:
            self.object_id = _generate_id()
        self.data = data
        self.name = f'id:{self.object_id} data:{self.data}'


class PBXTreeType:
    ABSOLUTE = '<absolute>'
    GROUP = '<group>'  #组
    BUILT_PRODUCTS_DIR = 'BUILT_PRODUCTS_DIR'
    DEVELOPER_DIR = 'DEVELOPER_DIR'
    SDKROOT = 'SDKROOT'
    SOURCE_ROOT = 'SOURCE_ROOT'

    @classmethod
    def options(cls):
        return [PBXTreeType.SOURCE_ROOT, PBXTreeType.SDKROOT, PBXTreeType.GROUP, PBXTreeType.ABSOLUTE, PBXTreeType.DEVELOPER_DIR, PBXTreeType.BUILT_PRODUCTS_DIR]


# PBX解析类
class PBXProjectHelper:

    def __init__(self, path,parse_in_mac=True):
        if os.path.exists(path):
            self.path = path
            self.root = {}
            self.pbxproj_path = os.path.abspath(path)  #工程配置文件目录
            self.source_root = os.path.abspath(os.path.join(os.path.split(path)[0], '..'))  #工程目录
            if parse_in_mac:
                self._parse_file_in_mac()
            else:
                self._parse_file()
            self.objects: dict = self.root["objects"]
            self.objects_ins: Dict[str, PBXObject] = {}
            self.project = self._getObject(self.root["rootObject"])
            self.mainGroup = self._getObject(self.project.data["mainGroup"])
            self.isas = {}  #文件类型列表
            for k, v in self.objects.items():
                isa = v["isa"]
                if isa not in self.isas:
                    self.isas[isa] = [k]
                else:
                    self.isas[isa].append(k)

        else:
            raise Exception(f'无效的PBX路径 = {path}')

    #plutil -convert json -s -r -o project.json  project.pbxproj
    #先转json，再load json
    def _parse_file_in_mac(self):
        json_path = os.path.join(self.source_root, 'project.json')
        if not os.path.exists(json_path):
            cmd = f'plutil -convert json -s -r -o {json_path} {self.path}'
            print(f'{cmd}')
            ret = os.system(cmd)
            if ret != 0:
                raise Exception("生成json  Error!")
        with open(json_path, 'r', encoding='UTF-8') as fp:
            self.root = json.load(fp)

    def _parse_file(self):
        with open(self.path, 'r', encoding='UTF-8') as fp:
            self.root = osp.OpenStepDecoder.ParseFromFile(fp)

    # 保存修改
    def save(self, savepath=None):
        # with open(os.path.join(os.curdir, "project_tmp.json"), 'w', encoding='UTF-8') as fb:
        #     json.dump(self.root, fb)
        # return
        projData = "//!$*UTF8*$!\n"
        projData += _dictToString(self.root, '')
        # 写入到文件
        if savepath is None:
            savepath = self.path
        with open(savepath, 'w', encoding='UTF-8') as fb:
            fb.write(projData)

    def _getObject(self, objId) -> PBXObject:
        if objId not in self.objects_ins:
            self.objects_ins[objId] = PBXObject(objId, self.objects[objId])
        return self.objects_ins[objId]

    # 移除对象
    def _delObject(self, obj: PBXObject):
        if obj.object_id in self.objects:
            del self.objects[obj.object_id]
            isa = obj.data["isa"]
            if isa in self.isas:
                self.isas[isa].remove(obj.object_id)

    #添加对象
    def _addObject(self, obj: PBXObject):
        if obj.object_id in self.objects:
            raise Exception(f'add object {obj.object_id} confilict')
        # print(f'add object:{obj.name}')
        self.objects[obj.object_id] = obj.data
        isa = obj.data["isa"]
        if isa not in self.isas:
            self.isas[isa] = [obj.object_id]
        else:
            self.isas[isa].append(obj.object_id)

    def _get_objs_by_isa(self, isa) -> List[PBXObject]:
        objects = self.isas[isa]
        res = []
        for item in objects:
            res.append(self._getObject(item))
        return res

    def _get_target_by_name(self, name) -> PBXObject:
        tagets = self._get_objs_by_isa("PBXNativeTarget")
        for item in tagets:
            if item.data["name"] == name:
                return item
        # raise Exception(f'get target failed target_name:{name}')
        return None

    def _get_config_list(self, target_name) -> List[PBXObject]:
        target = self._get_target_by_name(target_name)
        configlist_obj = self._getObject(target.data["buildConfigurationList"])
        configlist = configlist_obj.data["buildConfigurations"]
        res = []
        for config in configlist:
            res.append(self._getObject(config))
        return res

    def _getBuildPhase(self, target_name: str, isa: str) -> PBXObject:
        target = self._get_target_by_name(target_name)
        buildPhases_list = target.data["buildPhases"]
        for buildPhases in buildPhases_list:
            obj = self._getObject(buildPhases)
            if obj.data["isa"] == isa:
                return obj
        # raise Exception(f'get build phase failed target_name:{target_name} isa:{isa}')
        return None

    def _removeBuildPhases(self, target_name: str, target: PBXObject):
        target = self._get_target_by_name(target_name)
        buildPhases_list = target.data["buildPhases"]
        if target.object_id in buildPhases_list:
            buildPhases_list.poptarget.object_id()

    #name :名字  parent:父节点 isa:类型
    def _get_groups_by_name(self, name, parent: PBXObject = None, isa="PBXGroup") -> List[PBXObject]:
        groups = self._get_objs_by_isa(isa)
        groups = list(x for x in groups if _get_key(x.data, "name") == name)
        if parent:
            childs = _get_key(parent.data, "children")
            if childs:
                valid = []
                for group in groups:
                    if group.object_id in childs:
                        valid.append(group)
                return valid
            return []
        return groups

    #增加一个组,name:组名  path：路径  parent:父节点
    def add_group(self, name: str, path: str = "", parent: PBXObject = None, isa="PBXGroup") -> PBXObject:
        if parent is None:
            parent = self.mainGroup
        groups = self._get_groups_by_name(name, parent, isa)
        if len(groups) > 0:
            print(f'find group:{name}')
            return groups[0]
        print(f'add group:{name}')
        obj = PBXObject("", {'isa': isa, 'children': [], 'name': name, 'path': path, 'sourceTree': "<group>"})
        self._addObject(obj)
        self._add_child(parent, obj)
        return obj

    #添加为子节点
    def _add_child(self, parent: PBXObject = None, obj: PBXObject = None, key="children"):

        if parent is None:
            parent = self.mainGroup
        # print(f'add child:{obj.name} to :{parent.name} ')
        if key in parent.data:
            if obj.object_id not in parent.data[key]:
                parent.data[key].append(obj.object_id)
        else:
            parent.data[key] = [obj.object_id]

    #添加一个文件
    def add_file(self, target_name: str, path: str, parent: PBXObject, tree: str, settings: dict = None) -> PBXObject:
        abs_path = None
        if os.path.isabs(path):
            abs_path = path
            if not os.path.exists(path):
                raise Exception(f'file not exit:{path}')
            if tree in (PBXTreeType.GROUP, PBXTreeType.SOURCE_ROOT):
                path = os.path.relpath(path, self.source_root)  #获取相对路径
            else:
                tree = PBXTreeType.ABSOLUTE
        filename = os.path.split(path)[1]
        # file_short_name = os.path.splitext(filename)[0]
        # if tree in (TreeType.GROUP, TreeType.SOURCE_ROOT):
        #     filename = file_short_name
        filelist = self._get_objs_by_isa("PBXFileReference")

        file_ref_obj = None
        for file_item in filelist:
            tmp_name = _get_key(file_item.data, "name")
            tmp_path = _get_key(file_item.data, "path")
            tmp_sourceTree = _get_key(file_item.data, "sourceTree")
            if tmp_name == filename and tmp_path == path and tmp_sourceTree == tree:
                print(f'文件已经存在，不添加:{tmp_name} {tmp_path} {tmp_sourceTree}')
                file_ref_obj = file_item
                break

        file_type, buid_file_isa, fileEncoding = _determine_file_type(path)
        if file_ref_obj is None:
            file_ref_obj = PBXObject("", {'isa': "PBXFileReference", 'name': filename, 'path': path, 'sourceTree': tree})
            file_ref_obj.data["lastKnownFileType"] = file_type
            if fileEncoding:
                file_ref_obj.data["fileEncoding"] = fileEncoding
            self._addObject(file_ref_obj)

        self._add_child(parent, file_ref_obj)

        if buid_file_isa:
            self._addBuildFile(target_name, file_ref_obj, buid_file_isa, settings)

        if abs_path and os.path.exists(abs_path):
            library_path = os.path.join('$(SRCROOT)', os.path.split(path)[0])

            if os.path.isfile(abs_path):
                # print(f'add search flags:{library_path}')
                self.add_flag(target_name, "LIBRARY_SEARCH_PATHS", library_path)
            else:
                # print(f'add framework flags:{library_path}')
                self.add_flag(target_name, "FRAMEWORK_SEARCH_PATHS", library_path)

        return file_ref_obj

    #添加一个build file
    def _addBuildFile(self, target_name: str, file_obj: PBXObject, parent_isa: str, settings: dict = None) -> PBXObject:
        info = {'isa': "PBXBuildFile", "fileRef": file_obj.object_id}
        if settings:
            info["settings"] = settings
        obj = PBXObject("", info)
        build_parent = self._getBuildPhase(target_name, parent_isa)
        self._addObject(obj)
        self._add_child(build_parent, obj, "files")
        return obj

    #添加一个文件夹
    def add_folder(self, target_name: str, path: str, parent: PBXObject, excludes=None):
        if not os.path.isdir(path):
            raise Exception(f'add folder:{path} 失败,非文件夹')
        if not excludes:
            excludes = []
        path = os.path.abspath(path)
        dirname = os.path.split(path)[1]
        parent = self.add_group(dirname, path, parent)
        for child in os.listdir(path):
            if [pattern for pattern in excludes if re.match(pattern, child)]:
                continue

            full_path = os.path.join(path, child)
            filename = os.path.splitext(child)[1]
            if os.path.isfile(full_path) or filename in _SPECIAL_FOLDERS:
                # check if the file exists already, if not add it
                self.add_file(target_name, full_path, parent, tree=PBXTreeType.SOURCE_ROOT)
            else:
                self.add_folder(target_name, full_path, parent)

    def add_flags(self, target_name, flag_name, flags):
        for flag in flags:
            self.add_flag(target_name, flag_name, flag)

    #增加配置项
    def add_flag(self, target_name, flag_name, flag):
        configlist = self._get_config_list(target_name)
        for config in configlist:
            if 'buildSettings' not in config.data:
                config.data['buildSettings'] = {}
            config_dic = config.data['buildSettings']
            #初始化flagname
            if flag_name in config_dic:
                current_flags = config_dic[flag_name]
            else:
                config_dic[flag_name] = flag
                continue
            #添加flag
            if not isinstance(current_flags, list):
                current_flags = [current_flags]

            if flag in current_flags:
                continue
            config_dic[flag_name] = current_flags + [flag]

    #修改
    def set_flags(self, target_name, flag_name, flags):
        configlist = self._get_config_list(target_name)
        for config in configlist:
            if 'buildSettings' not in config.data:
                config.data['buildSettings'] = {}
            config_dic = config.data['buildSettings']
            config_dic[flag_name] = flags

    def remove_run_script(self, target_name, script_pattern):
        buildPhase = self._getBuildPhase(target_name, "PBXShellScriptBuildPhase")
        if buildPhase:
            script_text = _get_key(buildPhase.data, "shellScript")
            if script_text and re.match(script_pattern, script_text):
                self._removeBuildPhases(target_name, buildPhase)
                self._delObject(buildPhase)

    def set_swift_enable(self, target_name):
        self.set_flags(target_name, 'CLANG_ENABLE_MODULES', "YES")
        self.set_flags(target_name, 'SWIFT_OPTIMIZATION_LEVEL', "-Onone")
        self.set_flags(target_name, 'SWIFT_VERSION', "5.0")
        self.set_flags(target_name, 'ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES', "YES")
        self.set_flags(target_name, 'LD_RUNPATH_SEARCH_PATHS', "$(inherited) @executable_path/Frameworks")
        for _, value in self.project.data["attributes"]["TargetAttributes"].items():
            value["LastSwiftMigration"] = "1250"

    def _addRegion(self, region):
        regions = self.project.data["knownRegions"] or []
        reginalias = '"' + region + '"'
        if region not in regions:
            if reginalias not in regions:
                regions.append(region)
        self.project.data["knownRegions"] = regions

    #修改签名
    #"codesign": "Apple Development: Qiang Xie (3L7K7P4U8P)",
    #"profile": "hoc_20210830jp_dev",
    def change_code_sign(self, target_name, codesign, profile):
        self.set_flags(target_name, 'CODE_SIGN_IDENTITY[sdk=iphoneos*]', codesign)
        self.set_flags(target_name, 'CODE_SIGN_IDENTITY', codesign)
        self.set_flags(target_name, 'PROVISIONING_PROFILE_SPECIFIER', profile)
        self.set_flags(target_name, 'CODE_SIGN_STYLE', 'Manual')

    def add_lan(self, target_name, lanpath, lan_name):
        print(f'add lan:{lan_name} path:{lanpath}')
        projectfilepath = os.path.join(self.source_root, f'{lan_name}.lproj')
        remove_path(projectfilepath)
        shutil.copytree(lanpath, projectfilepath)
        self._addRegion(lan_name)
        find_res = self._get_groups_by_name("InfoPlist.strings", self.mainGroup, "PBXVariantGroup")
        if len(find_res) == 0:
            infoplist_group = self.add_group("InfoPlist.strings", "", None, "PBXVariantGroup")
            self._addBuildFile(target_name, infoplist_group, "PBXResourcesBuildPhase")
        else:
            infoplist_group = find_res[0]

        file_ref_obj = PBXObject("", {'isa': "PBXFileReference", 'name': lan_name, 'path': f'{lan_name}.lproj/InfoPlist.strings', 'sourceTree': PBXTreeType.GROUP})
        file_ref_obj.data["lastKnownFileType"] = "text.plist.strings"
        self._addObject(file_ref_obj)
        self._add_child(infoplist_group, file_ref_obj)

    def change_package_name(self, target_name, package_name: str):
        arr = package_name.split('.')
        product_name = arr[len(arr) - 1]
        # pre_name = arr.pop(-1).join('.')
        print(f'product_name:{product_name}')
        self.set_flags(target_name, 'PRODUCT_BUNDLE_IDENTIFIER', package_name)
        self.set_flags(target_name, 'PRODUCT_NAME', product_name)
