#!/usr/bin/python3
#coding:utf-8
from sys import argv,executable #获取外部传参和外置配置更新
from os import environ,path,name,makedirs,listdir,link,remove,removedirs,renames # os操作
from time import sleep,strftime,localtime,time # 时间相关
from datetime import datetime # 时间相减用
from re import findall,match,search,sub,I # 匹配相关
from shutil import move # 移动File
from ast import literal_eval # srt转化
from zhconv import convert # 繁化简
from urllib.parse import quote,unquote # url encode
from requests import get,post,exceptions # 网络部分
from random import randint # 随机数生成
from threading import Thread # 多线程
from importlib import import_module # 动态加载模块
#Start 开始部分进行程序的初始化 

def Start_PATH():# 初始化
    # 版本 数据库缓存 Api数据缓存 Log数据集 分隔符
    global Versions,AimeListCache,BgmAPIDataCache,TMDBAPIDataCache,LogData,Separator,Proxy,TgBotMsgData,PyPath
    Versions = '2.(11.5).0'
    AimeListCache = None
    BgmAPIDataCache = {}
    TMDBAPIDataCache = {}
    LogData = f'\n\n[{strftime("%Y-%m-%d %H:%M:%S",localtime(time()))}] INFO: Running....'
    Separator = '\\' if name == 'nt' else '/'
    TgBotMsgData = ''
    PyPath = __file__.replace('AutoAnimeMv.py','').strip(' ')
    Auxiliary_READConfig()
    Auxiliary_Log((f'当前工具版本为{Versions}',f'当前操作系统识别码为{name},posix/nt/java对应linux/windows/java虚拟机'),'INFO')

def Start_GetArgv():# 获取参数,判断处理模式
    ArgvNumber = len(argv)
    Auxiliary_Log(f'接受到的参数 > {argv}')
    if 2 <= ArgvNumber <= 3:# 接受1-2个参数
        if argv[1] == 'update' or argv[1] == 'updata': # 更新模式
            Auxiliary_Updata()
        elif argv[1] == 'help': #help
            Auxiliary_Help()
        elif path.exists(argv[1]) == True:# 批处理模式
            if ArgvNumber == 2:
                return argv[1], #待扫描目录
            else:
                return argv[1],argv[2] #待扫描目录和文件分类
        else:
            Auxiliary_Exit('参数出错')
    elif 4 <= ArgvNumber <= 5: #接受3-4参数
            if path.exists(argv[1]) == True:
                if ArgvNumber == 4: # 保存目录 种子名称 文件个数
                    return argv[1],argv[2],argv[3]
                else:# + 文件分类
                    return argv[1],argv[2],argv[3],argv[4]
            elif argv[1] == 'fixSE':
                    Auxiliary_FixSE(argv[2],argv[3],argv[4])# 需要修复的动漫目录 需要修复的剧季 修复之后的剧季
    else:
        Auxiliary_Help()
# Processing 进行程序的开始工作,进行核心处理
def Processing_Mode(ArgvData:list):# 模式选择
    ArgvNumber = len(ArgvData)
    global Path
    Path = ArgvData[0]
    if path.exists(Path) == True:
        # 批处理模式(非分类|分类) or Qb下载模式
        FileListTuporList = Auxiliary_ScanDIR(Path) if ArgvNumber <= 2 or (ArgvData[2] != '1') else [ArgvData[1]]
        Auxiliary_DeleteLogs()
        global CategoryName
        CategoryName = ''
        if ArgvNumber == 2:# 分类识别
            CategoryName = ArgvData[1]
        elif ArgvNumber == 4:
            CategoryName = ArgvData[3]

        if CategoryName != '':
            Auxiliary_Log(f'当前分类 >> {CategoryName}')

        if type(FileListTuporList) == tuple:
            return FileListTuporList # 文件列表元组(视频文件列表,字幕文件列表)
        else:
            for i in FileListTuporList:
                if path.isfile(f'{Path}{Separator}{i}') == False:
                    Auxiliary_Log(f'{Path}{Separator}{i} 不存在的文件','WARNING')
                    FileListTuporList.remove(i)
            if FileListTuporList != []:
                return FileListTuporList  # 元组中唯一有效的文件列表
            Auxiliary_Exit('没有有效的番剧文件')
    else:
        Auxiliary_Exit(f'不存在 {Path} 目录')
   
def Processing_Main(LorT):# 核心处理
    if type(LorT) == tuple: # (视频文件列表,字幕文件列表)
        for File in LorT[0]:
            try:
                flag = Processing_Identification(File)
                if flag == None:
                    break
                SE,EP,RAWSE,RAWEP,RAWName = flag
                ASSList = Auxiliary_IDEASS(RAWName,RAWSE,RAWEP,LorT[1])
                ApiName = Auxiliary_Api(RAWName)
                Sorting_Mv(File,RAWName,SE,EP,ASSList,ApiName)
            except Exception:
                continue
    else:# 唯一有效的文件列表
        for File in LorT:
            try:
                flag = Processing_Identification(File)
                if flag == None:
                    break
                SE,EP,RAWSE,RAWEP,RAWName = flag
                ApiName = Auxiliary_Api(RAWName)
                Sorting_Mv(File,RAWName,SE,EP,None,ApiName)
            except Exception:
                continue

def Processing_Identification(File:str):# 识别
    NewFile = Auxiliary_RMSubtitlingTeam(Auxiliary_RMOTSTR(Auxiliary_UniformOTSTR(File)))# 字符的统一加剔除
    AnimeFileCheckFlag = Auxiliary_AnimeFileCheck(NewFile)
    if AnimeFileCheckFlag == True:
        Auxiliary_Log('-'*80,'INFO')
        RAWEP = Auxiliary_IDEEP(NewFile)
        Auxiliary_Log(f'匹配出的剧集 ==> {RAWEP}','INFO')
        RAWName = Auxiliary_IDEVDName(NewFile,RAWEP)
        EP = '0' + RAWEP if (len(RAWEP) < 2 or ( '.' in RAWEP and RAWEP[0] != '0')) and (SEEPSINGLECHARACTER == False) else RAWEP# 美化剧集
        if '.' in RAWEP or RAWEP == '0' or RAWEP == '00':
            SE = '00' if SEEPSINGLECHARACTER == False else '0'
            RAWSE = ''
            Auxiliary_Log(f'特殊剧季 ==> {SE}','INFO')
            SeasonMatchData = r'(季(.*?)第)|(([0-9]{0,1}[0-9]{1})S)|(([0-9]{0,1}[0-9]{1})nosaeS)|(([0-9]{0,1}[0-9]{1}) nosaeS)|(([0-9]{0,1}[0-9]{1})-nosaeS)|(nosaeS-dn([0-9]{1}))'
            RAWName = sub(SeasonMatchData,'',RAWName[::-1],flags=I)[::-1].strip('-')
        else:
            SE,Name,RAWSE = Auxiliary_IDESE(RAWName)
            Auxiliary_Log(f'匹配出的剧季 ==> {RAWSE}','INFO')
            RAWName = RAWName if Name == None else Name
            SE = '0' + SE if len(SE) == 1 and SEEPSINGLECHARACTER == False else SE
        if SEEPSINGLECHARACTER == True:
            SE = SE.lstrip('0')
            EP = EP.lstrip('0')
        return SE,EP,RAWSE,RAWEP,RAWName
    else:
        Auxiliary_Log(f'当前文件属于{AnimeFileCheckFlag},跳过处理','INFO')

# Sorting 进行整理工作
def Sorting_Mv(FileName,RAWName,SE,EP,ASSList,ApiName):# 文件处理
    def FileML(src,dst):
        global TgBotMsgData
        if USELINK == True:
            try:
                link(src,dst)
                Auxiliary_Log(f'Link-{dst} << {src}','INFO')
                TgBotMsgData = TgBotMsgData + (f'Link-{src} << {dst}\n')
            except OSError as err:
                if '[WinError 1]' in str(err):
                    Auxiliary_Log('当前文件系统不支持硬链接','ERROR')
                    if LINKFAILSUSEMOVEFLAGS == True:
                        move(src,dst)
                        Auxiliary_Log(f'Move-{src} << {dst}')
                        TgBotMsgData= TgBotMsgData + (f'Move-{src} << {dst}\n')
                else:
                    Auxiliary_Exit(err)
        else:
            move(src,dst)
            Auxiliary_Log(f'Move-{dst} << {src}')
            TgBotMsgData = TgBotMsgData + (f'Move-{src} << {dst}\n')
    NewDir = f'{Path}{Separator}{CategoryName}{Separator}{ApiName}{Separator}Season{SE}{Separator}' if ApiName != None else f'{Path}{Separator}{CategoryName}{Separator}{RAWName}{Separator}Season{SE}{Separator}'
    NewName = f'S{SE}E{EP}' if USETITLTOEP != True else f'S{SE}E{EP}.{ApiName}'
    if path.exists(NewDir) == False:
        makedirs(NewDir)
    else:
        Auxiliary_Log(f'{NewDir}已存在','INFO')
    if ASSList != None:
        for ASSFile in ASSList:
            FileType = path.splitext(ASSFile)[1].lower()
            NewASSName = NewName + Auxiliary_ASSFileCA(ASSFile)
            if path.isfile(f'{NewDir}{NewASSName}{FileType}') == False:
                FileML(f'{Path}{Separator}{ASSFile}',f'{NewDir}{NewASSName}{FileType}')
            else:
                Auxiliary_Log(f'{NewDir}{NewASSName}{FileType}已存在,故跳过','WARNING')
    FileType = path.splitext(FileName)[1].lower()
    if path.isfile(f'{NewDir}{NewName}{FileType}') == False:
        NewName = NewName + Auxiliary_ASSFileCA(FileName) if FileType == '.ass' or FileType == '.str' else NewName
        FileML(f'{Path}{Separator}{FileName}',f'{NewDir}{NewName}{FileType}')
    else: 
        Auxiliary_Log(f'{NewDir}{NewName}{FileType}已存在,故跳过','WARNING')

# Auxiliary 其他辅助
def Auxiliary_Help(): # Help 
    global HELP
    Logo = '''     
     █████╗ ██╗   ██╗████████╗ ██████╗  █████╗ ███╗   ██╗██╗███╗   ███╗███████╗███╗   ███╗██╗   ██╗
    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗████╗  ██║██║████╗ ████║██╔════╝████╗ ████║██║   ██║
    ███████║██║   ██║   ██║   ██║   ██║███████║██╔██╗ ██║██║██╔████╔██║█████╗  ██╔████╔██║██║   ██║
    ██╔══██║██║   ██║   ██║   ██║   ██║██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══╝  ██║╚██╔╝██║╚██╗ ██╔╝
    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║  ██║██║ ╚████║██║██║ ╚═╝ ██║███████╗██║ ╚═╝ ██║ ╚████╔╝ 
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝  ╚═══╝                                                                                            
    '''
    HELP = '\n* 欢迎使用AutoAnimeMv，这是一个番剧自动识别剧名剧集+自动重命名+自动整理的工具\n* Github URL：https://github.com/Abcuders/AutoAnimeMv\n* 一般使用方法请见Github Docs，有两种模式：\n   1.批处理模式，会将目录内的番剧自动整理并放到"番剧所在目录/分类/番剧名/剧季/剧集.mkv",\n     其中分类可以是相对路径，比如设置为"../"，就会将"番剧名"放到"番剧所在目录"的同一级目录。\n\n    python3 AutoAnimeMv.py 番剧所在目录 [分类]\n\n   2.qbit模式，在qbit中设置下载完成后执行程序，并填入下面的命令，\n    注意AutoAnimeMv.py要填写脚本的绝对路径，传入的参数为qbit的下载预设参数。\n    参数解释：%D:保存路径 %N:Torrent名称 %C:文件数 %L:分类(也可以用相对路径)\n\n    python3 AutoAnimeMv.py "%D" "%N" "%C" "%L"(可选)\n\n* 以下是不常用的使用方法：\n    python3 AutoAnimeMv.py [help] [updata] [fixSE]\n* 参数解释：\n    help 打印出Help {help}\n    updata,update  更新AutoAnimeMv.py {updata}\n    fixSE 修复错乱的剧季 {fixSE 需要修复的番剧目录 需要修复的剧季 修复之后的剧季}\n* 配置文件config.ini：windows自行重命名文件，linux中执行下列命令：\n    cp config.ini.Template config.ini'
    print(Logo + '\n' + '-'*100 +  HELP)
    quit()

def Auxiliary_FixSE(Path,OLDSE,NEWSE):
    OLDSE = '0' + OLDSE if len(OLDSE) == 1 and SEEPSINGLECHARACTER == False else OLDSE
    NEWSE = '0' + NEWSE if len(NEWSE) == 1 and SEEPSINGLECHARACTER == False else NEWSE
    FilePath = f'{Path}{Separator}Season{OLDSE}{Separator}'
    NewPath = f'{Path}{Separator}Season{NEWSE}{Separator}'
    if path.exists(FilePath) == True:
        if path.exists(NewPath) == True:
            print(listdir(NewPath))
            if listdir(NewPath) == []:
                Auxiliary_Log(f'存在剧季{NEWSE},但内容为空','WARNING')
                removedirs(NewPath)
            else:
                Auxiliary_Exit(f'存在剧季{NEWSE},内容不为空')
        Auxiliary_Log('开始进行番剧剧季的纠错')
        FileListTuporList = Auxiliary_ScanDIR(FilePath,1)
        if type(FileListTuporList[0]) == list:
            for Filelist in FileListTuporList:
                for File in Filelist:
                    NewFile = NewPath + File.replace(f'S{OLDSE}',f'S{NEWSE}')
                    renames(FilePath + File,NewFile)
                    Auxiliary_Log(f'{NewFile} << {File}')
        else:
            for File in FileListTuporList:
                NewFile = NewPath + File.replace(f'S{OLDSE}',f'S{NEWSE}')
                renames(FilePath + File,NewFile)
                Auxiliary_Log(f'{NewFile} << {File}')
        Auxiliary_Exit('番剧纠错完毕')

    else:
        Auxiliary_Exit(f'不存在 {Path} 目录')

def Auxiliary_Notice(Msg): # 共享内存
    if 'USERTGBOT' in globals():
        global USERTGBOT
        if USERTGBOT == True:
            if 'USERBOTNOTICE' in globals():
                global USERBOTNOTICE
                if USERBOTNOTICE == True: 
                    from mmap import mmap,ACCESS_WRITE
                    from contextlib import closing
                    with open(f'{PyPath}{Separator}CS.dat', 'r+') as f:
                        with closing(mmap(f.fileno(), 1024, access=ACCESS_WRITE)) as m:
                            m.seek(0)
                            Msg.rjust(1024,'\x00')
                            m.write(bytearray(Msg.encode()))
                            Auxiliary_Log('Notice消息已发送')
                            m.flush()

def Auxiliary_LoadModule():
    ModuleFileList = []
    for FileName in listdir('./Ext'):
        File = path.splitext(FileName)
        if File[-1] == '.py' or File[-1] == '.PY':
            ModuleFileList.append(File[0])
        #elif File[-1] == '.ini' or File[-1] == '.INI':
    if ModuleFileList != []:
        Auxiliary_Log(f'存在{len(ModuleFileList)}个模块 >> {ModuleFileList}')
        for ModuleName in ModuleFileList:
            Module = import_module(f'Ext.{ModuleName}')
            #[[FuncName,Func],]
            for func in Module.func(globals()):
                globals()[func[0]] = func[1]
                Auxiliary_Log(f'模块 << {func[0]}')
    

def Auxiliary_READConfig():# 读取外置Config.ini文件并更新
    global USEMODULE,HTTPPROXY,HTTPSPROXY,ALLPROXY,USEBGMAPI,USETMDBAPI,USELINK,LINKFAILSUSEMOVEFLAGS,USETITLTOEP,PRINTLOGFLAG,RMLOGSFLAG,USEBOTFLAG,TIMELAPSE,SEEPSINGLECHARACTER,JELLYFINFORMAT,HELP,MATCHORGANIZED
    USEMODULE = None
    HTTPPROXY = '' # Http代理
    HTTPSPROXY = '' # Https代理
    ALLPROXY = '' # 全部代理
    USEBGMAPI = True # 使用BgmApi
    USETMDBAPI = True # 使用TMDBApi
    USELINK = False # 使用硬链接开关
    JELLYFINFORMAT = False # jellyfin 使用 ISO/639 标准 简体和繁体都使用chi做标识\
    USETITLTOEP = False # 给每个番剧视频加上番剧Title 
    LINKFAILSUSEMOVEFLAGS = False #硬链接失败时使用MOVE
    PRINTLOGFLAG = False # 打印log开关
    RMLOGSFLAG = '7' # 日志文件超时删除,填数字代表删除多久前的
    USEBOTFLAG = False # 使用TgBot进行通知
    TIMELAPSE = 0 # 延时处理番剧
    SEEPSINGLECHARACTER = False
    MATCHORGANIZED = False #对已经整理为S0E0这种格式的番剧重新匹配并整理，慎开
    HELP = None # HELP 
    if path.isfile(f'{PyPath}{Separator}config.ini'):
        with open(f'{PyPath}{Separator}config.ini','r',encoding='UTF-8') as ff:
            Auxiliary_Log('正在读取外置ini文件','INFO')
            T = 0
            COEFLAG = False
            for i in ff.readlines():
                i = i.strip('\n') 
                if i != '' and i[0] != '#':
                    ii = i.split("=",1)[0].strip('- ')
                    if ii in globals():
                        Auxiliary_Log(f'配置 < {i}','INFO')
                        exec(f'global {ii};{i}')
                    T = T + 1
                elif i == '#mtf' or i == '#ftm':
                    COEFLAG = True
            if T == 0:
                Auxiliary_Log('外置ini文件没有配置','WARNING')
            elif COEFLAG == True:
                COE()

        Auxiliary_PROXY()

        if USEMODULE == True:
            Auxiliary_LoadModule()

    if int(TIMELAPSE) != 0:
        Auxiliary_Log(f'正在{TIMELAPSE}秒延时中')
        sleep(int(TIMELAPSE))

def Auxiliary_Log(Msg,MsgFlag='INFO',flag=None,end='\n'):# 日志
    global LogData,PRINTLOGFLAG
    Msg = Msg if type(Msg) == tuple else (Msg,)
    for OneMsg in Msg:
        Msg = f'[{strftime("%Y-%m-%d %H:%M:%S",localtime(time()))}] {MsgFlag}: {OneMsg}'
        if PRINTLOGFLAG == True or flag == 'PRINT':
            print(Msg,end=end)         
        LogData = LogData + '\n' + Msg

def Auxiliary_DeleteLogs():# 日志清理
    RmLogsList = []
    if RMLOGSFLAG != False and 'LogsFileList' in globals() and LogsFileList != []:
        ToDay = datetime.strptime(datetime.now().strftime('%Y-%m-%d'),"%Y-%m-%d").date()
        for Logs in LogsFileList:
            LogDate =  datetime.strptime(Logs.strip('.log'),"%Y-%m-%d").date()
            if (ToDay - LogDate).days >= int(RMLOGSFLAG):
                remove(f'{Path}{Separator}{Logs}')
                RmLogsList.append(Logs)
        if RmLogsList != []:
            Auxiliary_Log(f'清理了保存时间达到和超过{RMLOGSFLAG}天的日志文件 << {RmLogsList}')


def Auxiliary_WriteLog():# 写log文件
    LogPath = argv[1] if path.exists(argv[1]) == True else PyPath
    if LogPath == PyPath:
        Auxiliary_Log(f'Log文件保存在工具目录下','WARNING')
    with open(f'{LogPath}{Separator}{strftime("%Y-%m-%d",localtime(time()))}.log','a+',encoding='UTF-8') as LogFile:
        LogFile.write(LogData)

def Auxiliary_UniformOTSTR(File):# 统一意外字符
    NewFile = convert(File,'zh-hans')# 繁化简
    if MATCHORGANIZED == True:
        NewFile = sub(r'^(S\d{1,2})?(E\d{1,4})\.?(.+)(?=\..+$)',r'\3\1\2',NewFile,flags=0)   #处理s00e00在开头名字， 比如使用该脚本处理过的文件也再次处理
        NewFile = sub(r'(?<!\d)\.(?!\d|(mkv|mp4|ass|srt|log))',' ',NewFile,flags=0) #将.替换为空格，但排除前或后有数字的和文件格式后缀
        NewFile = sub(r'(?<=.)(S\d{1,2})?(?<=.)E(\d{1,4})',r'\1 \2E ',NewFile,flags=I)
    NewUSTRFile = sub(r',|，| ','-',NewFile,flags=I) 
    NewUSTRFile = sub('[^a-z0-9\s&/\-:：.\(\)（）《》\u4e00-\u9fa5\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF]','=',NewUSTRFile,flags=I)
    #异种剧集统一
    OtEpisodesMatchData = ['第(\d{1,4})集','(\d{1,4})集','第(\d{1,4})话','(\d{1,4})END','(\d{1,4}) END','(\d{1,4})E']
    for i in OtEpisodesMatchData:
        if search(i,NewUSTRFile,flags=I) != None:
            a = search(i,NewUSTRFile,flags=I)
            NewUSTRFile = NewUSTRFile.replace(a.group(),a.group(1).strip('\u4e00-\u9fa5'))
    return NewUSTRFile

def Auxiliary_RMOTSTR(File):# 剔除意外字符
    NewPSTRFile = File
    #匹配待去除列表
    FuzzyMatchData = [r'(.*?|=)月新番(.*?|=)',r'\d{4}.\d{2}.\d{2}',r'20\d{2}',r'v[2-9]',r'\d{4}年\d{1,2}月番']
    #精准待去除列表
    PreciseMatchData = ['仅限港澳台地区','国漫','x264','1080p','720p','4k','\(-\)','（-）','hevc.?10bit',' 10bit','[xh]265.?10bit','[xh]265']
    for i in PreciseMatchData:
        NewPSTRFile = sub(r'%s'%i,'-',NewPSTRFile,flags=I)
    for i in FuzzyMatchData:
        NewPSTRFile = sub(i,'-',NewPSTRFile,flags=I)
    return NewPSTRFile

def Auxiliary_IDESE(File):# 识别剧季并截断Name
    SeasonMatchData = r'(季(.*?)第)|(([0-9]{0,1}[0-9]{1})S)|(([0-9]{0,1}[0-9]{1})nosaeS)|(([0-9]{0,1}[0-9]{1}) nosaeS)|(([0-9]{0,1}[0-9]{1})-nosaeS)|(nosaeS-dn([0-9]{1}))'
    if search(SeasonMatchData,File[::-1],flags=I) != None:
        SEData = findall(SeasonMatchData,File[::-1],flags=I)
        SENamelist = []
        SEList = []
        for sedata in SEData:
            for se in sedata:# 取值
                if se != '' and se.isnumeric() == False:
                    SENamelist.append(se[::-1])
                #elif len(se) == 1:
                #    SEList.append(se)
                elif se.isnumeric() == True: # 判断数字
                    SEList.append(se)
        for i in SENamelist:# 截断Name
            File = sub(r'%s.*'%i,'',File,flags=I).strip('-') #通过剧季截断文件名
        for i in range(len(SEList)):
            if SEList[i].isdecimal() == True: # 判断纯数字
                SE = SEList[i][::-1]
            elif '\u0e00' <= SEList[i] <= '\u9fa5':# 中文剧季转化
                digit = {'一':'01', '二':'02', '三':'03', '四':'04', '五':'05', '六':'06', '七':'07', '八':'08', '九':'09','壹':'01','贰':'02','叁':'03','肆':'04','伍':'05','陆':'06','柒':'07','捌':'08','玖':'09'}
                SE = digit[SEList[i]]
            return SE,File,SENamelist[0]
    else:
        return '01',File,''

def Auxiliary_IDEEP(File):# 识别剧集
    try:
        if findall(r'[^0-9a-z.\u4e00-\u9fa5\u0800-\u4e00](\d{1}\.[0-9]{1,4})[^0-9a-uw-z.\u4e00-\u9fa5\u0800-\u4e00]',File[::-1],flags=I) != []:
            Episodes = findall(r'[^0-9a-z.\u4e00-\u9fa5\u0800-\u4e00](\d{1}\.[0-9]{1,4})[^0-9a-uw-z.\u4e00-\u9fa5\u0800-\u4e00]',File[::-1],flags=I)[0][::-1].strip(" =-_eEv")
        else:
            Episodes = findall(r'[^0-9a-z.\u4e00-\u9fa5\u0800-\u4e00][0-9]{1,4}[^0-9a-uw-z.\u4e00-\u9fa5\u0800-\u4e00]',File[::-1],flags=I)[0][::-1].strip(" =-_eEv")
    except IndexError:
        Auxiliary_Log('未匹配出剧集,请检查(程序目前不支持电影动漫)','WARNING')
        return Episodes
    else:
        #Auxiliary_Log(f'匹配出的剧集 ==> {Episodes}','INFO')
        return Episodes

def Auxiliary_RMSubtitlingTeam(File):# 剔除字幕组信息
    File = File.strip('-')
    if File[0] == '《':# 判断有无字幕组信息
        File = sub(r'《|》','',File,flags=I) 
    else:
        File = sub(r'^=.*?=','',File,flags=I)
    return File

def Auxiliary_IDEVDName(File,RAWEP):# 识别剧名
    #VDName = sub(r'.*%s'%RAWEP[::-1],'',File[::-1],count=0,flags=I).strip('=-=-=-')[::-1]
    VDName = search(r'%s(.*)'%RAWEP[::-1],File[::-1],flags=I).group(1).strip('=-=-=-')[::-1]
    Auxiliary_Log(f'通过剧集截断文件名 ==> {VDName}','INFO')
    return VDName

def Auxiliary_IDEASS(File,SE,EP,ASSList):# 识别当前番剧视频的所属字幕文件
    ASSFileList = []
    for ASSFile in ASSList:
        ASSName = Auxiliary_UniformOTSTR(ASSFile)
        ASSEP = Auxiliary_IDEEP(ASSName)
        if File in ASSName and EP == ASSEP and SE in ASSName:
            ASSFileList.append(ASSFile)
    ASSFileList = None if ASSFileList == [] else ASSFileList
    return ASSFileList

def Auxiliary_ScanDIR(Dir,Flag=0):# 扫描文件目录,返回文件列表
    def Scan(Dir,File):
        for ii in SuffixList:
                if match(ii[::-1],File[::-1],flags=I) != None:
                    if ii == '.ass' or ii == '.srt':
                        AssFileList.append(File)
                    elif ii == '.log':
                        LogsFileList.append(File)
                    else:
                        VDFileList.append(File)

    global LogsFileList
    SuffixList = ['.ass','.srt','.mp4','mkv','.log']
    AssFileList = []
    VDFileList = []
    LogsFileList = []
    for File in listdir(Dir):# 扫描目录,并按文件类型分类
        if Flag == 0 and ((MATCHORGANIZED == True) or (search(r'S\d{1,2}E\d{1,4}',File,flags=I) == None)):   #判断是否对已整理的文件进行再次整理
            Scan(Dir,File)
        elif Flag == 1 and search(r'S\d{1,2}E\d{1,4}',File,flags=I) != None:
            Scan(Dir,File)

    if  VDFileList != []:# 判断模式,处理字幕还是视频
        if AssFileList != []:
            Auxiliary_Log((f'发现{len(AssFileList)}个字幕文件 ==> {AssFileList}',f'发现{len(VDFileList)}个视频文件 ==> {VDFileList}'),'INFO')
            return VDFileList,AssFileList
        else:
            Auxiliary_Log(f'发现{len(VDFileList)}个视频文件,没有发现字幕文件, ==> {VDFileList}','INFO')
            return VDFileList
    elif AssFileList != []:
        Auxiliary_Log((f'没有发现任何番剧视频文件,但发现{len(AssFileList)}个字幕文件 ==> {AssFileList}','只有字幕文件需要处理'),'INFO')
        return AssFileList
    else:
        Auxiliary_Exit('没有任何番剧文件')

def Auxiliary_AnimeFileCheck(File):# 检查番剧文件
    Checklist = ['OP','CM','SP','PV']
    for i in Checklist:
        if search(f'[-=]{i}[-=]',File,flags=I) != None:
            return i
    return True         

def Auxiliary_ASSFileCA(ASSFile):# 字幕文件的语言分类
    SubtitleList = [['简','sc','chs','GB'],['繁','tc','cht','BIG5'],['日','jp']]
    for i in range(len(SubtitleList)):
        for ii in SubtitleList[i]:
            if search(ii[::-1],ASSFile[::-1],flags=I) != None:
                if i == 0:
                    return '.chs' if JELLYFINFORMAT == False else '.简体中文.chi'
                elif i == 1:
                    return '.cht' if JELLYFINFORMAT == False else '.繁体中文.chi'
                elif i == 2:
                    return '.jp'
    return '.other'

def Auxiliary_PROXY(): # 代理
    if 'HTTPPROXY' in globals():
        global HTTPPROXY
        environ['http_proxy'] = HTTPPROXY
    if 'HTTPSPROXY' in globals():
        global HTTPSPROXY
        environ['https_proxy'] = HTTPSPROXY
    if 'ALLPROXY' in globals():
        global ALLPROXY
        environ['all_proxy'] = ALLPROXY

def Auxiliary_Http(Url,flag='GET',json=None):# 网络
    headers = {'User-Agent':f'Abcuders/AutoAnimeMv/{Versions}(https://github.com/Abcuders/AutoAnimeMv)'}
    if 'themoviedb' in Url:
        headers['Authorization'] = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0MjkxYzA0NGYyZTNmMThhYzQ3NzNjNzU1YzM3NzA5OSIsInN1YiI6IjY0MjZlMTg1YTNlNGJhMDExMTQ5OGI2MSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Q0Rn4QdnCelhzozE07jgUQwJFzdJrLXGhaSBphnzYuQ"
    try:
        if flag != 'GET':
            HttpData = post(Url,json,headers=headers) 
        else:
            HttpData = get(Url,headers=headers)
    except exceptions.ConnectionError:
        Auxiliary_Exit(f'访问 {Url} 失败,未能获取到内容,请检查您是否启用了系统代理,如是则您应该在此工具中配置代理信息,否则您则需要检查您的网络能否访问')
    except Exception as err:
        Auxiliary_Exit(f'访问 {Url} 失败,未能获取到内容,请检查您的网络 {err}')
    if HttpData.status_code == 200:
        return HttpData.text
    else:
        Auxiliary_Exit('HttpData Status Code != 200')

def Auxiliary_Updata():# 更新
    Updata = Auxiliary_Http('https://raw.githubusercontent.com/Abcuders/AutoAnimeMv/main/AutoAnimeMv.py')
    if search(r"Versions = '(\d{1}.\d{1,4}.\d{1,4})'",Updata,flags=I) != None:
        if Versions != search(r"Versions = '(\d{1}.\d{1,4}.\d{1,4})'",Updata,flags=I).group(1):
            with open('AutoAnimeMv.py','w+',encoding='UTF-8') as UpdataFile:
                UpdataFile.write(Updata)
                Auxiliary_Exit('更新完成')
        else:
            Auxiliary_Exit('当前即是最新版本')
    else:
        Auxiliary_Exit('更新数据存在问题')

def Auxiliary_Api(Name):   
    def BgmApi(Name):# BgmApi相关,返回一个标准的中文名称
        global USEBGMAPI,BgmAPIDataCache
        if USEBGMAPI == True:
            if Name not in BgmAPIDataCache:
                try:
                    BgmApiData = literal_eval(Auxiliary_Http(f"https://api.bgm.tv/search/subject/{Name}?type=2&responseGroup=small&max_results=1"))
                except:
                    Auxiliary_Log(f'BgmApi没有检索到关于 {Name} 内容','WARNING')
                    return None
                else:
                    if 'BgmApiData' != None:
                        ApiName = unquote(BgmApiData['list'][0]['name_cn'],encoding='UTF-8',errors='replace') if unquote(BgmApiData['list'][0]['name_cn'],encoding='UTF-8',errors='replace') != '' else unquote(BgmApiData['list'][0]['name'],encoding='UTF-8',errors='replace')
                        ApiName = sub('第.*?季','',ApiName,flags=I).strip('- []【】 ')
                        Auxiliary_Log(f'{ApiName} << bgmApi查询结果')
                        BgmAPIDataCache[Name] = ApiName
                        return ApiName
                    else:
                        return None
            else:
                Auxiliary_Log(f'{BgmAPIDataCache[Name]} << bgmApi缓存查询结果')
                return BgmAPIDataCache[Name]
        else:
            Auxiliary_Log('没有使用BgmApi进行检索')
            return None

    def TMDBApi(Name):# TMDBApi相关,返回一个标准的中文名称
        global USETMDBAPI,TMDBAPIDataCache
        if USETMDBAPI == True:
            if Name not in TMDBAPIDataCache:
                TMDBApiData = literal_eval(Auxiliary_Http(f'https://api.themoviedb.org/3/search/tv?query={Name}&include_adult=true&language=zh&page=1').replace('false','False').replace('true','True').replace('null','None'))
                if TMDBApiData['results'] != []:
                    for MDBApiTV in TMDBApiData['results']:
                        ApiName = MDBApiTV['name']
                        ApiName = sub('第.*?季','',ApiName,flags=I).strip('- []【】 ')
                        Auxiliary_Log(f'{ApiName} << TMDBApi查询结果')
                        TMDBAPIDataCache[Name] = ApiName
                        return ApiName
                else:
                    Auxiliary_Log(f'TMDBApi没有检索到关于 {Name} 内容','WARNING')
                    return None
            else:
                Auxiliary_Log(f'{TMDBAPIDataCache[Name]} << TMDBApi缓存查询结果')
                return TMDBAPIDataCache[Name]
        else:
            Auxiliary_Log('没有使用TMDBApi进行检索')
            return None

    if search(r'([\u4e00-\u9fa5]+)',Name.replace('-',''),flags=I) != None: # 获取匹配到的汉字
        Name = search(r'([\u4e00-\u9fa5]+)',Name.replace('-',''),flags=I).group(1) 
        BGMApiName = BgmApi(Name)
        TMDBApiName = TMDBApi(BGMApiName if BGMApiName != None else Name)
               
    else:
        BGMApiName = BgmApi(Name)
        TMDBApiName = TMDBApi(BGMApiName if BGMApiName != None else Name)

    if BGMApiName == None and TMDBApiName == None:
        if USEBGMAPI == True or USETMDBAPI == True:
    #        Auxiliary_Log('Api识别失败现在进行额外的API识别')
            Auxiliary_Exit('Api识别失败')
    #        StrList = Name.split('-')
    #    else:
    #        ApiName = None
    else:
        ApiName = TMDBApiName if TMDBApiName != None else BGMApiName
    return ApiName.replace(' ','') if ApiName != None else ApiName

def Auxiliary_Exit(LogMsg):# 因可预见错误离场
    Auxiliary_Log(LogMsg,'EXIT',flag='PRINT')
    exit()

# 模块路标
#def Signpost_():

# Colored Eggs
def COE():#
    Auxiliary_Log('你的存在千真万确毋需置疑,我们一直都在这里,我们一直会爱你,愿每一个人都能自由的生活在阳光下','AAM')

if __name__ == '__main__':
    start = time()
    try:
        Start_PATH()
        ArgvData = Start_GetArgv()
        Processing_Main(Processing_Mode(ArgvData))
    except Exception as err:
        Auxiliary_Log(f'没有预料到的错误 > {err}','ERROR',flag='PRINT')
    else:
        end = time()
        Auxiliary_Log(f'一切工作已经完成,用时{end - start}','INFO',flag='PRINT')
        Auxiliary_Notice('新的番剧已处理完成')
    finally:
        if HELP == None:
            Auxiliary_WriteLog()
