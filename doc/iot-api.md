# 0x01.  

BASE_URL = [http://tianji.qiweiwangguo.com](http://tianji.qiweiwangguo.com/) 

服务器异常返回通常 Status code 为400+，格式如下

```json
{
  "error": "错误提示",
  "code": 1000
}
```



#### 1. 获取设备(列表) {#devices}

GET: BASE_URL/iot/device

| 参数        | 描述                                                   | 类型 | 是否必须 | 示例  |
| ----------- | ------------------------------------------------------ | ---- | -------- | ----- |
| device      | 设备编号，添加该参数获取单个设备信息，反之获取设备列表 | Int  | 否       | 23000 |
| free-master | 过滤出没有配对过的设备或没有从设备的主设备             | Bool | 否       | 1     |
| free-device | 过滤出没有配对过的设备                                 | Bool | 否       | 1     |
| p           | 页码，默认第一页                                       | Int  | 否       | 1     |
| n           | 每页显示数据，默认每页显示10条数据                     | Int  | 否       | 10    |

返回参数

| 参数                | 描述                                                         | 类型   | 示例   |
| ------------------- | ------------------------------------------------------------ | ------ | ------ |
| device_name         | 设备编号                                                     | Int    | 23000  |
| hardware_version    | 硬件版本号                                                   | String | v0.2.0 |
| ident_boot_version  | 硬件识别程序 Boot 版本                                       | String | v0.2.0 |
| ident_file_hash     | 硬件识别特征值文件 Hash                                      | String | MD5值  |
| ident_file_version  | 特征值文件版本号                                             | String |        |
| ident_version       | 硬件识别程序版本                                             | String | v0.2.0 |
| logical_channel     | 逻辑信道，0~255                                              | Int    |        |
| master              | 主设备编号，若无或为0则尚未配置主从                          | Int    |        |
| slave               | 从设备编号，若无或为0则该设备无从设备或未配置                | Int    |        |
| master_slave        | NOT_SET: 未设置<br />MASTER：单个主设备<br />MASTER_WITH_SLAVE：主设备 <br />SLAVE：从设备 | String |        |
| online              | -1: 未激活 0：离线 1：在线                                   | Int    |        |
| physical_channel    | 物理信道，1~254                                              | Int    |        |
| script              | 脚本名称                                                     | String |        |
| script_hash         | 脚本文件 Hash                                                | String |        |
| sim                 | SIM 卡号                                                     | String |        |
| sync_boot_version   | 硬件同步程序 Boot 版本                                       | String |        |
| sync_delay          | 主从同步延时秒数                                             | Int    |        |
| sync_version        | 硬件同步程序版本号                                           | String |        |
| working_status      | 工作状态 0：空闲 1：同步中                                   | Int    |        |
| new_script          | 需要下载的脚本名称                                           | String |        |
| new_sync            | 需要下载的同步器固件版本号                                   | String |        |
| new_ident           | 需要下载的识别固件版本号                                     | String |        |
| new_ident_file      | 需要下载的识别特征值文件版本号                               | String |        |
| download_script     | 脚本下载状态 -1：失败 0：下载成功 1：下载中                  | Int    |        |
| download_sync       | 同步器固件下载状态 -1：失败 0：下载成功 1：下载中            | Int    |        |
| download_ident      | 识别固件下载状态 -1：失败 0：下载成功 1：下载中              | Int    |        |
| download_ident_file | 特征值文件下载状态 -1：失败 0：下载成功 1：下载中            | Int    |        |



#### 2. 编辑设备 {#edit_device}

PUT: BASE_URL/iot/device

| 参数             | 描述                             | 类型   | 是否必须 | 示例   |
| ---------------- | -------------------------------- | ------ | -------- | ------ |
| master_device    | 主设备编号                       | Int    | 是       | 23000  |
| slave_device     | 从设备编号                       | Int    | 否       | 同上   |
| cinema           | 影院名称                         | String | 否       | 奥斯卡 |
| cinema_id        | 影院 ID                          | Int    | 否       |        |
| hall             | 影厅名称                         | String | 否       |        |
| hall_id          | 影厅 ID                          | Int    | 否       |        |
| master_slave     | 是否配置主从，-1不配置，0或1配置 | Int    | 是       |        |
| physical_channel | 物理信道，1~254                  | Int    | 否       |        |
| logical_channel  | 逻辑信道，0~255                  | Int    | 否       |        |
| script           | 脚本名称                         | String | 否       |        |
| script_id        | 脚本 ID                          | Int    | 否       |        |
| script_hash      | 脚本 Hash，目前为 MD5 值         | String | 否       |        |

#### 3. 升级设备 {#upgrade_device}

PUT: BASE_URL/iot/device/firmware

| 参数    | 描述             | 类型   | 是否必须 | 示例          |
| ------- | ---------------- | ------ | -------- | ------------- |
| device  | 设备编号         | Int    | 是       | 23000         |
| type    | 升级类型         | String | 是       | SYNC_FIRMWARE |
| version | 升级文件版本号   | String | 是       | v1.0.0        |
| hash    | 升级文件 Hash 值 | String | 是       | MD5 值        |
| script  | 脚本名称         | String | 否       |               |

升级文件类型现有 4 种：

```
SYNC_FIRMWARE：同步程序固件
IDENT_FIRMWARE：识别程序固件
IDENT_FILE：特征值文件
SCRIPT：脚本文件
```

**若升级脚本文件则 version 字段对应的是脚本 ID，Int 类型**

#### 4. 获取设备配置 {#device_config}

POST: BASE_URL/iot/device/config

| 参数 | 描述           | 类型   | 是否必须 | 示例 |
| ---- | -------------- | ------ | -------- | ---- |
| sn   | 硬件唯一序列号 | String | 是       |      |

返回参数

| 参数        | 描述            | 类型   | 示例                                   |
| ----------- | --------------- | ------ | -------------------------------------- |
| client_id   | 客户端 ID       | String | 23001...                               |
| username    | 用户名          | String | 23001&a1LKBWmhOFE                      |
| passwd      | 密码            | String | 204EB4CC3108696D96C8310DBD8991         |
| mqtt_broker | MQTT 服务器地址 | String | x.iot-as-mqtt.cn-shanghai.aliyuncs.com |

##### 5. 解绑设备 {#unbind_device}

PUT: BASE_URL/iot/device/unbind

| 参数   | 描述       | 类型 | 是否必须 | 示例  |
| ------ | ---------- | ---- | -------- | ----- |
| device | 主设备编号 | Int  | 是       | 23000 |

