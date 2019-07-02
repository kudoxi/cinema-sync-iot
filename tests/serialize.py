from app.core.serialize import *


if __name__ == '__main__':
    spia = SyncProtocolInstructionAssembler()
    spda = SyncProtocolDataAnalyser()
    ttt = bytes.fromhex("3839383630343430313131384333373138313137")
    print(str(ttt, encoding="UTF-8"))
    print(spia.load(
        ProtocolInstructions.UPGRADE,
        type_id=UpgradeType.SCRIPT,
        resource_id="123",
        resource_md5="ffffffffffffffffffffffffffffffff",
        server_ip="192.168.5.32",
        server_port=123,
    ).hex())
    val_set = spia.load(
        ProtocolInstructions.ATTR_SET,
        master_slave=MasterSlaveType.MASTER_WITH_SLAVE,
        sync_delay=123,
        physical_channel=22,
        channel=23,
    ).hex()
    print("ATTR_SET", val_set)
    print(spia.load(
        ProtocolInstructions.UPGRADE,
        type_id=UpgradeType.IDENT_FILE,
        resource_id="v0.23.32",
        resource_md5="ffffffffffffffffffffffffffffffff",
        server_ip="192.168.5.32",
        server_port=123,
    ).hex())
    print(spda.dump(spia.simulate_resp_attr_read()))
    print(spda.dump(spia.simulate_resp_query_script()))
    print(spda.dump(spia.simulate_resp_attr_set()))
    print(spda.dump(spia.simulate_resp_remote_operations()))
    print(spda.dump(spia.simulate_resp_report_state()))
    print(spda.dump(spia.simulate_resp_resource_download_broadcast()))
