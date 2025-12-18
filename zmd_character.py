# -*- coding: utf-8 -*-
import random
from multiprocessing import Pool, cpu_count
import math

class GachaCharacter(object):
    def __init__(self):
        # 角色池
        # 基础参数
        self.six_star_rate = 0.008      # 基础6星角色概率 0.8%
        self.up_rate = 0.5              # up6星角色概率 50% (出6星时有50%是up)
        self.pity_threshold = 65        # 6星概率开始增长的抽数阈值 (出6星后重置概率，第66抽才开始增加)
        self.rate_increase = 0.05       # 每抽6星概率增长 5%

        self.soft_pity = 80             # 小保底 80抽 (连续未出6星80抽必出6星)
        self.hard_pity = 120            # 大保底 120抽 (连续未出up120抽必出up，只作用一次，出up后消失)
        self.free_pity = 240            # 每240的整数倍都会送一个up (这个赠送的up不影响小保底等等卡池机制，纯额外赠送)

        self.five_star_rate = 0.08      # 5星角色概率 8%
                                        # 4星角色概率为1.0-6星概率-5星概率(动态变化，6星概率增长时会缩减4星概率，5星概率维持不变)

        self.five_star_soft_pity = 10   # 连续10抽不出5星或以上，则第10抽必出5星

        self.six_star_weapon_ticket = 2000  # 抽到6星角色会获得2000武器池票
        self.five_star_weapon_ticket = 200  # 抽到5星角色会获得200武器池票
        self.four_star_weapon_ticket = 20   # 抽到4星角色会获得20武器池票

        # 计数器
        self.total_pulls = 0                # 总抽数
        self.six_star_count = 0             # 6星数量
        self.up_six_star_count = 0          # UP6星数量
        self.last_six_star_pull = 0         # 上次出6星的抽数
        self.last_up_six_star_pull = 0      # 上次出UP的抽数

        self.five_star_count = 0            # 5星数量
        self.last_five_star_pull = 0        # 上次出5星的抽数

        self.four_star_count = 0            # 4星数量

        self.has_hard_pity = True           # 是否还有大保底
        self.force_up = False               # 是否强制up

        self.weapon_ticket = 0              # 当前武器票数量

    def pull_one(self):
        """
        单次抽卡
        返回: (星级, 是否UP)
        """
        self.total_pulls += 1
        current_pull = self.total_pulls

        # 检查是否有免费UP
        if current_pull % self.free_pity == 0:
            # 免费UP不影响其他保底机制
            self.up_six_star_count += 1

        # 计算当前6星概率
        pulls_since_six_star = current_pull - self.last_six_star_pull
        if pulls_since_six_star >= self.pity_threshold:
            six_star_rate = self.six_star_rate + (pulls_since_six_star - self.pity_threshold) * self.rate_increase
        else:
            six_star_rate = self.six_star_rate

        # 软保底：80抽必出6星
        if pulls_since_six_star >= self.soft_pity:
            six_star_rate = 1.0

        # 大保底检查
        if self.has_hard_pity and (current_pull - self.last_up_six_star_pull) >= self.hard_pity:
            self.force_up = True
            six_star_rate = 1.0

        # 5星概率
        pull_since_five_star = current_pull - self.last_five_star_pull
        if pull_since_five_star >= self.five_star_soft_pity:
            five_star_rate = 1.0
        else:
            five_star_rate = self.five_star_rate + six_star_rate

        # 抽卡判定
        pull_rate = random.random()
        if pull_rate <= six_star_rate:
            # 出6星
            self.six_star_count += 1
            self.last_six_star_pull = current_pull
            self.last_five_star_pull = current_pull # 抽到6星也会同时重置5星的10抽保底

            # 判定是否UP
            is_up = self.force_up or (random.random() <= self.up_rate)

            if is_up:
                self.up_six_star_count += 1
                self.last_up_six_star_pull = current_pull
                self.has_hard_pity = False  # 出UP后大保底机制消失
                self.force_up = False
            self.weapon_ticket += self.six_star_weapon_ticket
            return (6, is_up)
        elif pull_rate <= five_star_rate:
            # 未出6星
            self.five_star_count += 1
            self.last_five_star_pull = current_pull
            self.weapon_ticket += self.five_star_weapon_ticket
            return (5, False)  # 简化非6星掉落逻辑
        else:
            self.four_star_count += 1
            self.weapon_ticket += self.four_star_weapon_ticket
            return (4, False)

def single_simulation(target_up_count):
    """
    单次模拟函数，用于并行处理
    返回获得指定数量UP所需的抽数
    """
    gacha = GachaCharacter()
    
    # 持续抽卡直到获得目标数量的UP
    while gacha.up_six_star_count < target_up_count:
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
    
    print "\n获得{}只UP角色的统计信息:".format(target_up_count)
    print "期望抽数: {:.2f}抽".format(avg_pulls)
    print "中位数: {:.2f}抽".format(median_pulls)
    print "方差: {:.2f}".format(variance)
    print "标准差: {:.2f}".format(std_deviation)
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
    print "\n获得{}只UP角色所需抽数分布:".format(target_up_count)
    print "-" * 50
    print("{:<16} {:<12} {:<12} {:<15}".format("抽数区间", "人数", "分位数", "占比(%)"))
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
            cumulative_percentage_str = "{:<7.2f}".format(cumulative_percentage)

            print "{:<10} {:<10} {:<10} {:<15}".format(
                "{}-{}".format(bins[i], bins[i]+9),
                count,
                cumulative_percentage_str,
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
    target_up_counts = [1,]

    # 确定并行进程数
    num_processes = min(cpu_count(), 4)  # 限制最多使用4个进程，避免过度占用CPU
    
    print "=" * 50
    print "开始终末地角色模拟计算..."
    print "=" * 50
    print "模拟次数: {}".format(num_simulations)

    for target_up_count in target_up_counts:
        print "\n正在计算获得{}只UP的分布...".format(target_up_count)
        
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
    gacha = GachaCharacter()  # 创建实例只是为了访问参数
    print "  基础6星概率: {}%".format(gacha.six_star_rate * 100)
    print "  UP6星概率: {}%".format(gacha.up_rate*100)
    print "  软保底: {}抽必出6星".format(gacha.soft_pity)
    print "  大保底: {}抽必出UP".format(gacha.hard_pity)
    print "  免费UP: 每{}抽送1个UP".format(gacha.free_pity)
    print "=" * 50

if __name__ == "__main__":
    # 设置随机数种子以确保结果可重现
    random.seed()
    simulate_gacha_distribution(1000000)
