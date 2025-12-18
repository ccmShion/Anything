# -*- coding: utf-8 -*-
import random
import math
from mc_character import GachaCharacter
from mc_weapon import GachaWeapon
from multiprocessing import Pool, cpu_count

def single_simulation_combined(args):
    """
    单次模拟函数，用于并行处理
    返回获得指定数量UP角色和UP武器所需的抽数
    """
    character_count, weapon_count = args
    # 创建新的角色池和武器池实例
    char_gacha = GachaCharacter()
    weapon_gacha = GachaWeapon()
    
    # 模拟直到达到目标
    while (char_gacha.up_five_star_count < character_count or weapon_gacha.up_five_star_count < weapon_count):
        # 抽角色池
        if char_gacha.up_five_star_count < character_count:
            char_gacha.pull_one()

        # 抽武器池
        if weapon_gacha.up_five_star_count < weapon_count:
            weapon_gacha.pull_one()
    
    # 返回总抽数（只需要角色抽数，因为武器是用票抽的）
    return char_gacha.total_pulls + weapon_gacha.total_pulls

def simulate_optimized_strategy(character_count, weapon_count, num_simulations=100000):
    """
    模拟优化策略：利用角色抽卡获得的武器票抽取武器
    :param character_count: 需要的UP角色数量
    :param weapon_count: 需要的UP武器数量
    :param num_simulations: 模拟次数
    :return: 平均抽数列表
    """
    
    # 确定并行进程数
    num_processes = min(cpu_count(), 4)  # 限制最多使用4个进程，避免过度占用CPU
    
    print("模拟次数: {}".format(num_simulations))
    
    # 使用进程池进行并行计算
    try:
        pool = Pool(processes=num_processes)
        tasks = [(character_count, weapon_count)] * num_simulations
        results = pool.map(single_simulation_combined, tasks)
        pool.close()
        pool.join()
        
        return results

    except Exception as e:
        print("并行计算出错: {}".format(e))
        # 出错时回退到串行计算
        total_pulls_list = []
        for i in range(num_simulations):
            # 创建新的角色池和武器池实例
            char_gacha = GachaCharacter()
            weapon_gacha = GachaWeapon()
            
            # 模拟直到达到目标
            while (char_gacha.up_five_star_count < character_count or weapon_gacha.up_five_star_count < weapon_count):
                # 抽角色池
                if char_gacha.up_five_star_count < character_count:
                    char_gacha.pull_one()

                # 抽武器池
                if weapon_gacha.up_five_star_count < weapon_count:
                    weapon_gacha.pull_one()

            # 返回总抽数（只需要角色抽数，因为武器是用票抽的）
            return char_gacha.total_pulls + weapon_gacha.total_pulls

def calculate_variance(data, mean):
    """
    计算方差
    """
    if len(data) <= 1:
        return 0
    return sum((x - mean) ** 2 for x in data) / float(len(data))

def calculate_median(data):
    """
    计算中位数
    """
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n % 2 == 0:
        return (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2.0
    else:
        return sorted_data[n//2]

def create_distribution_report(data, character_count, weapon_count, num_simulations):
    """
    创建分布报告（打印形式）
    """
    # 计算基本统计数据
    avg_pulls = sum(data) / float(len(data))
    median_pulls = calculate_median(data)
    variance = calculate_variance(data, avg_pulls)
    std_deviation = math.sqrt(variance)
    
    print("\n获得{}个UP角色+{}把UP武器的统计信息:".format(character_count, weapon_count))
    print("期望抽数: {:.2f}抽".format(avg_pulls))
    print("中位数: {:.2f}抽".format(median_pulls))
    print("方差: {:.2f}".format(variance))
    print("标准差: {:.2f}".format(std_deviation))
    # 计算并显示指定百分位数的抽数
    sorted_data = sorted(data)
    percentiles = [10, 25, 50, 75, 90]
    print("\n分位数信息:")
    print("-" * 30)
    for p in percentiles:
        index = int((p / 100.0) * (len(sorted_data) - 1))
        percentile_value = sorted_data[index]
        print("{}% 分位数: {} 抽".format(p, int(percentile_value)))

    # 按10抽为单位分组
    max_pulls = max(data) if data else 0
    if max_pulls == 0:
        print("无有效数据")
        return
    
    # 创建区间
    bins = range(1, max_pulls + 11, 10)
    histogram = [0] * (len(bins) - 1)
    max_pull_histogram = 0
    
    # 统计各区间的数量
    for pulls in data:
        bin_index = min(pulls // 10, len(histogram) - 1)
        histogram[bin_index] += 1
        if pulls == max_pulls:
            max_pull_histogram += 1
    
    # 打印分布表
    print("\n获得{}个UP角色+{}把UP武器所需抽数分布:".format(character_count, weapon_count))
    print("-" * 50)
    print("{:<16} {:<12} {:<12} {:<15}".format("抽数区间", "人数", "分位数", "占比(%)"))
    print("-" * 50)
    
    cumulative = 0
    max_bin_count = 0
    max_bin_range = ""

    for i in range(len(histogram)):
        count = histogram[i]
        if count > 0:
            percentage = count * 100.0 / num_simulations
            cumulative += count
            cumulative_percentage = cumulative * 100.0 / num_simulations
            
            # 记录最大人数的区间
            if count > max_bin_count:
                max_bin_count = count
                max_bin_range = "{}-{}".format(bins[i], bins[i]+9)

            # 按每1%添加星星
            stars = "█" * int(percentage / 1)
            percentage_str = "{:<7.2f}{}".format(percentage, stars)
            cumulative_percentage_str = "{:<7.2f}".format(cumulative_percentage)
            
            print("{:<10} {:<10} {:<10} {:<15}".format(
                "{}-{}".format(bins[i], bins[i]+9), 
                count,
                cumulative_percentage_str,
                percentage_str
            ))
    
    # 添加额外保底数据展示
    max_pulls_percentage = max_pull_histogram * 100.0 / num_simulations
    if max_pulls_percentage >= 5.0:  # 占比超过5%就展示
        print("-" * 50)
        print("保底数据(保底人数大于5%时显示):")
        print("{:<10} {:<10} {:<15.2f}".format(
            "{}-{}".format(max_pulls-9, max_pulls),
            max_pull_histogram,
            max_pulls_percentage
        ))
    
    print("-" * 50)
    print("累计人数: {}".format(cumulative))
    print("累计占比: {:.2f}%".format(cumulative_percentage if 'cumulative_percentage' in locals() else 0))
    print("最大抽数区间: {} (人数: {}, 占比: {:.2f}%)".format(
        max_bin_range, max_bin_count, max_bin_count * 100.0 / num_simulations))
    print("=" * 50)

def main():
    # 模拟次数
    num_simulations = 1000000

    # 定义要计算的目标组合
    targets = [
        (1, 1),  # 1个角色+1把武器
        # (2, 1),  # 2个角色+1把武器
    ]
    
    print("\n" + "=" * 70)
    print("开始鸣潮角色+武器模拟计算...")
    print("=" * 70)

    # 对每个目标组合进行模拟
    for character_count, weapon_count in targets:
        print("\n" + "=" * 50)
        print("目标: {}个UP角色 + {}把UP武器".format(character_count, weapon_count))
        print("=" * 50)

        total_pulls_list = simulate_optimized_strategy(character_count, weapon_count, num_simulations)
        create_distribution_report(total_pulls_list, character_count, weapon_count, num_simulations)

if __name__ == "__main__":
    random.seed()
    main()
