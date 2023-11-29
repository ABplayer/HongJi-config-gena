def generate_vs_command(vs_address, vs_name, port, session_persistence, algorithm):
    base_command = f"slb virtual-address {vs_address}_va {vs_address}\n{{\n\tprofile logging default\n\tport {port} "

    if session_persistence.lower() == '否':
        command = base_command + f"tcp\n\t{{\n\t\tname {vs_name}\n\t\tsource-nat interface\n\t\tpool Pool_{vs_name}\n\t\tpath-persist\n\t\tprofile tcp tcp\n\t}}\n}}"
    elif algorithm == "源地址保持":
        command = base_command + f"tcp\n\t{{\n\t\tname {vs_name}\n\t\tsource-nat interface\n\t\tpool Pool_{vs_name}\n\t\tpath-persist\n\t\tprofile tcp tcp\n\t\tprofile persist source-ip source_addr_1800\n\t}}\n}}"
    elif algorithm == "cookie会话保持":
        command = base_command + f"http\n\t{{\n\t\tname {vs_name}\n\t\tsource-nat interface\n\t\tpool Pool_{vs_name}\n\t\tpath-persist\n\t\tprofile http http\n\t\tprofile connection-multiplex one-cnnection\n\t\tprofile persist cookie my_cookie_1800\n\t}}\n}}"

    return command

def generate_pool_command(pool_name, members, is_http, http_name, get_path, response_code, probe_port):
    node_commands = ""
    member_commands = ""
    for member_address, member_port in members:
        node_commands += f"slb node {member_address} {member_address}\n"
        member_commands += f"\tmember {member_address}:{member_port}\n"

    pool_command = ""
    if not is_http:
        pool_command = f"slb pool Pool_{pool_name} tcp\n{{\n\tmethod service-least-connection\n\thealth-check tcp\n{member_commands}}}\n"
    else:
        health_check_command = f"health check HTTP_{http_name} interval 5 retry 3 timeout 5 up-check-cnt 1\n{{\n\twait-all-retry\n\tmethod http port {probe_port} url GET /{get_path} response response-code {response_code}\n}}\n\n"
        pool_command = f"slb pool Pool_{pool_name} http\n{{\n\tmethod service-least-connection\n\thealth-check HTTP_{http_name}\n{member_commands}}}\n"
        pool_command = health_check_command + pool_command

    return node_commands + pool_command


vs_data = []
pool_data = []

def add_vs():
    vs_address = input("请输入VS地址: ")
    vs_name = input("请输入VS名称: ")
    port = input("请输入端口号: ")
    session_persistence = input("是否需要会话保持？(是/否): ")

    algorithm = ""
    if session_persistence.lower() == '是':
        algorithm = input("请输入会话保持算法（源地址保持/cookie会话保持）: ")

    vs_info = (vs_address, vs_name, port, session_persistence, algorithm)
    vs_data.append(vs_info)
    return generate_vs_command(vs_address, vs_name, port, session_persistence, algorithm)

def add_pool():
    pool_name = input("请输入POOL名称: ")
    members = []
    while True:
        member_address = input("请输入成员地址（输入'完成'结束添加）: ")
        if member_address.lower() == '完成':
            break
        member_port = input("请输入成员端口: ")
        members.append((member_address, member_port))

    app_type = input("这是TCP应用还是HTTP应用？(TCP/HTTP): ")
    is_http = app_type.lower() == "http"

    http_name = get_path = response_code = probe_port = ""
    if is_http:
        http_name = input("请输入HTTP探测名称: ")
        get_path = input("请输入GET地址: ")
        response_code = input("请输入返回码: ")
        probe_port = input("请输入探测端口: ")

    pool_info = (pool_name, members, is_http, http_name, get_path, response_code, probe_port)
    pool_data.append(pool_info)
    return generate_pool_command(pool_name, members, is_http, http_name, get_path, response_code, probe_port)


def main():
    commands = ""

    while True:
        add_pool()
        if input("是否添加另一个POOL？(是/否): ").lower() != '是':
            break

    while True:
        add_vs()
        if input("是否添加另一个VS？(是/否): ").lower() != '是':
            break

    for pool in pool_data:
        commands += generate_pool_command(*pool) + "\n"

    for vs in vs_data:
        commands += generate_vs_command(*vs) + "\n"

    with open("vs_command.txt", "w") as file:
        file.write(commands)

    print("所有命令已生成并保存到vs_command.txt文件中。")

main()



