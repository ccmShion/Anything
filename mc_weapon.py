# -*- coding: utf-8 -*-
import random
from multiprocessing import Pool, cpu_count
import math

class GachaWeapon(object):
    def __init__(self):
        # 基础参数
        self.base_rate = 0.008              # 基础5星武器概率 0.8%
        self.up_rate = 1.0                  # up5星武器概率 100% (出5星时有100%是up)
        self.pity_threshold_1 = (66, 70)    # 概率开始增长的抽数阈值1 (出5星后重置概率，第66~70抽之间增加)
        self.rate_increase_1 = 0.04         # 每抽概率增长 4%
        self.pity_threshold_2 = (71, 75)    # 概率开始增长的抽数阈值2 (出5星后重置概率，第71~75抽之间增加)
        self.rate_increase_2 = 0.08         # 每抽概率增长 8%
        self.pity_threshold_3 = (76, 79)    # 概率开始增长的抽数阈值3 (出5星后重置概率，第76~79抽之间增加)
        self.rate_increase_3 = 0.10         # 每抽概率增长 10%

        self.soft_pity = 79                 # 小保底 79抽 (连续未出5星79抽必出UP5星)

        # 计数器
        self.total_pulls = 0                # 总抽数
        self.five_star_count = 0            # 5星数量
        self.up_five_star_count = 0         # UP5星数量
        self.last_five_star_pull = 0        # 上次出5星的抽数
        self.last_up_five_star_pull = 0     # 上次出UP的抽数

    def pull_one(self):
        """
        单次抽卡
        返回: (星级, 是否UP)
        """
        self.total_pulls += 1
        current_pull = self.total_pulls

        # 计算当前5星概率
        pulls_since_five_star = current_pull - self.last_five_star_pull
        
        # 基础概率
        five_star_rate = self.base_rate
        
        # 根据抽数增加概率
        if self.pity_threshold_1[0] <= pulls_since_five_star <= self.pity_threshold_1[1]:
            five_star_rate += (pulls_since_five_star - self.pity_threshold_1[0] + 1) * self.rate_increase_1
        elif self.pity_threshold_2[0] <= pulls_since_five_star <= self.pity_threshold_2[1]:
            five_star_rate += (self.pity_threshold_1[1] - self.pity_threshold_1[0] + 1) * self.rate_increase_1 + \
                             (pulls_since_five_star - self.pity_threshold_2[0] + 1) * self.rate_increase_2
        elif self.pity_threshold_3[0] <= pulls_since_five_star <= self.pity_threshold_3[1]:
            five_star_rate += (self.pity_threshold_1[1] - self.pity_threshold_1[0] + 1) * self.rate_increase_1 + \
                             (self.pity_threshold_2[1] - self.pity_threshold_2[0] + 1) * self.rate_increase_2 + \
                             (pulls_since_five_star - self.pity_threshold_3[0] + 1) * self.rate_increase_3

        # 软保底：79抽必出5星
        if pulls_since_five_star >= self.soft_pity:
            five_star_rate = 1.0

        # 抽卡判定
        if random.random() <= five_star_rate:
            # 出5星
            self.five_star_count += 1
            self.last_five_star_pull = current_pull

            # 5星武器必定UP
            is_up = True
            if is_up:
                self.up_five_star_count += 1
                self.last_up_five_star_pull = current_pull

            return (5, is_up)
        else:
            # 未出5星
            return (random.choice([3, 4]), False)  # 简化非5星掉落逻辑


def single_simulation(target_up_count):
    """
    单次模拟函数，用于并行处理
    返回获得指定数量UP所需的抽数
    """
    gacha = GachaWeapon()
    
    # 持续抽卡直到获得目标数量的UP
    while gacha.up_five_star_count < target_up_count:
        gacha.pull_one()
    
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
    print "{:<16} {:<12} {:<15}".format("抽数区间", "人数", "占比(%)")
    print "-" * 50
    
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
            
            print "{:<10} {:<10} {:<15}".format(
                "{}-{}".format(bins[i], bins[i]+9), 
                count, 
                percentage_str
            )
    
    # 添加额外保底数据展示
    max_pulls_percentage = max_pull_histogram * 100.0 / num_simulations
    if max_pulls_percentage >= 5.0:  # 占比超过5%就展示
        print "-" * 50
        print "保底数据(保底人数大于5%时显示):"
        print "{:<10} {:<10} {:<15.2f}".format(
            "{}-{}".format(max_pulls, max_pulls),
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
    target_up_counts = [1, 2, 3, 4, 5, 6, 7]

    # 确定并行进程数
    num_processes = min(cpu_count(), 4)  # 限制最多使用4个进程，避免过度占用CPU
    
    print "=" * 50
    print "开始鸣潮武器模拟计算..."
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
    gacha = GachaWeapon()  # 创建实例只是为了访问参数
    print "  基础5星概率: {}%".format(gacha.base_rate*100)
    print "  UP5星概率: {}%".format(gacha.up_rate*100)
    print "  软保底: {}抽必出5星".format(gacha.soft_pity)
    print "  大小保底: 上一个5星非UP，则下一个5星必定为UP"
    print "=" * 50

if __name__ == "__main__":
    # 设置随机数种子以确保结果可重现
    random.seed()
    simulate_gacha_distribution(1000000)
