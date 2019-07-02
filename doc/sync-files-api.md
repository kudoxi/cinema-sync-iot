# 0x01. 物联网 API 列表

BASE_URL = [http://tianji.qiweiwangguo.com](http://tianji.qiweiwangguo.com/) 

服务器异常返回通常 Status code 为400+，格式如下

```json
{
  "error": "错误提示",
  "code": 1000
}
```



#### 1. 获取文件(列表) {#list}

GET: BASE_URL/sync/files

| 参数   | 描述                                                   | 类型 | 是否必须 | 示例  |
| ------ | ------------------------------------------------------ | ---- | -------- | ----- |
| type   | 文件类型                                                | Int  | 否       | 23000 |
| md5      | MD5值                                             | String  | 否       |      |
| filename | 文件名                                        | String  | 否       |     |
| p      | 页码，默认第一页                                       | Int  | 否       | 1     |
| n      | 每页显示数据，默认每页显示10条数据                     | Int  | 否       | 10    |

返回参数

| 参数               | 描述                                              | 类型   | 示例   |
| ----------------- | ------------------------------------------------- | ------ | ------ |
| id                | 编号                                              | Int    | 23000  |
| filename          | 文件名称                                            | String | app42.bin |
| file_size         | 文件大小（字节）                                    | Int | 1234 |
| md5               | MD5值                                              | String |   |
| type              | 升级文件类型，数字                                  | Int | 0 |
| type_describe     | 升级文件类型，类别名称                               | String    |  SYNC_FIRMWARE     |
| version           | 文件版本                                            | String    | v1.2.3       |
| uploaded_at       | 上传时间                                            | String    | 2017-11-11 11:11:11.333      |

升级文件类型现有 3 种：

```
SYNC_FIRMWARE：同步程序固件
IDENT_FIRMWARE：识别程序固件
IDENT_FILE：特征值文件
```

#### 2. 上传文件 {#upload}

POST: BASE_URL/sync/files

表单上传

| 参数    | 描述                                                   | 类型 | 是否必须 | 示例  |
| ------  | ------------------------------------------------------ | ---- | -------- | ----- |
| type    | 文件类型                                                | Int  | 是       | 0 |
| version | 文件版本                                           | String  | 是       | v1.2.3     |
| binfile | 文件                                        | file  | 是       |     |


升级文件类型现有 3 种：

```
0 SYNC_FIRMWARE：同步程序固件
2 IDENT_FIRMWARE：识别程序固件
3 IDENT_FILE：特征值文件
```

#### 3. 删除文件 {#delete}

DELETE: BASE_URL/sync/files/{id}

| 参数    | 描述             | 类型   | 是否必须 | 示例          |
| ------- | ---------------- | ------ | -------- | ------------- |
| id  | 列表中的文件编号         | Int    | 是       | 23000         |


