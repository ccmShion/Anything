# -*- coding: utf-8 -*-
import random
from multiprocessing import Pool, cpu_count
import math

class GachaWeapon(object):
    def __init__(self):
        # 武器池
        # 基础参数
        self.draw_need_ticket = 1980 # 需要1980武器票才能抽一次十连

        self.base_rate = 0.04       # 基础6星武器概率 4%
        self.up_rate = 0.25         # up6星武器概率 25% (出6星时有25%是up)

        self.soft_pity = 40         # 小保底 40抽 (连续未出6星40抽必出6星)
        self.hard_pity = 80         # 大保底 80抽 (连续未出up80抽必出up)

        # 计数器
        self.total_pulls = 0                # 总抽数
        self.six_star_count = 0             # 6星数量
        self.up_six_star_count = 0          # UP6星数量
        self.last_six_star_pull = 0         # 上次出6星的抽数
        self.last_up_six_star_pull = 0      # 上次出UP的抽数
        self.force_up = False               # 是否强制up

    def pull_ten(self):
        """
        十连抽卡
        返回: 本次十连抽获得的UP6星数量
        """
        up_count = 0
        for i in range(10):
            self.total_pulls += 1
            current_pull = self.total_pulls

            # 计算当前6星概率
            pulls_since_six_star = current_pull - self.last_six_star_pull
            six_star_rate = self.base_rate

            # 软保底：40抽必出6星
            if pulls_since_six_star >= self.soft_pity:
                six_star_rate = 1.0

            # 大保底检查
            if (current_pull - self.last_up_six_star_pull) >= self.hard_pity:
                self.force_up = True
                six_star_rate = 1.0

            # 抽卡判定
            if random.random() <= six_star_rate:
                # 出6星
                self.six_star_count += 1
                self.last_six_star_pull = current_pull

                # 判定是否UP
                is_up = self.force_up or (random.random() <= self.up_rate)

                if is_up:
                    self.up_six_star_count += 1
                    up_count += 1
                    self.last_up_six_star_pull = current_pull
                    self.force_up = False

        return up_count

def single_simulation(target_up_count):
    """
    单次模拟函数，用于并行处理
    返回获得指定数量UP所需的抽数
    """
    gacha = GachaWeapon()
    
    # 持续抽卡直到获得目标数量的UP
    while gacha.up_six_star_count < target_up_count:
        gacha.pull_ten()  # 只能十连抽
    
    return gacha.total_pulls

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

def create_distribution_report(data, target_up_count, num_simulations):
    """
    创建分布报告（打印形式）
    """
    # 计算基本统计数据
    avg_pulls = sum(data) / float(len(data))
    median_pulls = calculate_median(data)
    variance = calculate_variance(data, avg_pulls)
    std_deviation = math.sqrt(variance)
    
    print "\n获得{}把UP武器的统计信息:".format(target_up_count)
    print "期望抽数: {:.2f}抽".format(avg_pulls)
    print "中位数: {:.2f}抽".format(median_pulls)
    print "方差: {:.2f}".format(variance)
    print "标准差: {:.2f}".format(std_deviation)

    # 按10抽为单位分组
    max_pulls = max(data) if data else 0
    if max_pulls == 0:
        print "无有效数据"
        return
    
    # 创建区间
    bins = range(1, max_pulls + 11, 10)
    histogram = [0] * (len(bins) - 1)
    max_pull_histogram = 0
    
    # 统计各区间的数量
    for pulls in data:
        bin_index = min((pulls - 1) // 10, len(histogram) - 1)
        histogram[bin_index] += 1
        if pulls == max_pulls:
            max_pull_histogram += 1
    
    # 打印分布表
    print "\n获得{}把UP武器所需抽数分布:".format(target_up_count)
    print "-" * 50
    print "{:<12} {:<13} {:<13} {:<15}".format("抽数", "人数", "分位数", "占比(%)")
    print "-" * 50
    
    cumulative = 0
    max_bin_count = 0
    max_bin_range = ""
    
    for i in range(len(histogram)):
        count = histogram[i]
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

        print "{:<10} {:<10} {:<10} {:<15}".format(
            "{}".format(bins[i]+9),
            count,
            cumulative_percentage_str,
            percentage_str,
        )
    
    # 添加额外保底数据展示
    max_pulls_percentage = max_pull_histogram * 100.0 / num_simulations
    if max_pulls_percentage >= 5.0:  # 占比超过5%就展示
        print "-" * 50
        print "保底数据(保底人数大于5%时显示):"
        print "{:<10} {:<10} {:<15.2f}".format(
            "{}".format(max_pulls),
            max_pull_histogram,
            max_pulls_percentage
        )
    
    print "-" * 50
    print "累计人数: {}".format(cumulative)
    print "累计占比: {:.2f}%".format(cumulative_percentage if 'cumulative_percentage' in locals() else 0)
    print "最大抽数区间: {} (人数: {}, 占比: {:.2f}%)".format(
        max_bin_range, max_bin_count, max_bin_count * 100.0 / num_simulations)
    print "=" * 50

def simulate_gacha_distribution(num_simulations=10000):
    """
    模拟抽卡分布并生成报告
    """
    target_up_counts = [1, ]

    # 确定并行进程数
    num_processes = min(cpu_count(), 4)  # 限制最多使用4个进程，避免过度占用CPU
    
    print "=" * 50
    print "开始终末地武器模拟计算..."
    print "=" * 50
    print "模拟次数: {}".format(num_simulations)

    for target_up_count in target_up_counts:
        print "\n正在计算获得{}把UP的分布...".format(target_up_count)
        
        # 使用进程池进行并行计算
        try:
            pool = Pool(processes=num_processes)
            tasks = [target_up_count] * num_simulations
            results = pool.map(single_simulation, tasks)
            pool.close()
            pool.join()
        except Exception as e:
            print "并行计算出错: {}".format(e)
            continue
        
        # 生成分布报告
        create_distribution_report(results, target_up_count, num_simulations)
    
    print "\n参数设置:"
    gacha = GachaWeapon()  # 创建实例把是为了访问参数
    print "  基础6星概率: {}%".format(gacha.base_rate*100)
    print "  UP6星概率: {}%".format(gacha.up_rate*100)
    print "  软保底: {}抽必出6星".format(gacha.soft_pity)
    print "  大保底: {}抽必出UP".format(gacha.hard_pity)
    print "  抽卡模式: 十连抽"
    print "=" * 50

if __name__ == "__main__":
    # 设置随机数种子以确保结果可重现
    random.seed()
    simulate_gacha_distribution(1000000)
