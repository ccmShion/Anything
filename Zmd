# -*- coding: utf-8 -*-
import math
import os
import random

class POOL(object):
    def __init__(self, draw_count=1):
        # 基础参数
        self.base_rate = 0.008      # 基础6星角色概率 0.8%
        self.up_rate = 0.5          # up6星角色概率 50%
        self.pity_threshold = 65    # 概率开始增长的抽数阈值
        self.rate_increase = 0.05   # 每抽概率增长 5%

        self.soft_pity = 80         # 小保底 80抽
        self.hard_pity = 120        # 大保底 120抽

        self.draw_count = draw_count    # 下多少次池子

    # 单抽
    def pull_single(self):
        all_pull_count = [] # 目标up数所用的所有抽数
        star6_pull_count = 0 # 连续多少次没出6星（可跨池继承）
        for _ in xrange(self.draw_count):
            total_pull_count = 0 # 这次下池获得up的抽数
            # 120次单抽
            for _ in xrange(self.hard_pity):
                total_pull_count += 1
                star6_pull_count += 1
                cur_rate = random.random()

                is_up, star6_rate = self.get_star6_rate(star6_pull_count, total_pull_count)
                if cur_rate < star6_rate:
                    star6_pull_count = 0
                    # 抽到up立刻停手
                    if is_up:
                        all_pull_count.append(total_pull_count)
                        break

        return all_pull_count

    # 十连
    def pull_ten(self):
        all_pull_count = [] # 目标up数所用的所有抽数
        star6_pull_count = 0 # 连续多少次没出6星（可跨池继承）
        for _ in xrange(self.draw_count):
            total_pull_count = 0 # 这次下池获得up的抽数
            # 12次十连
            for _ in xrange(self.hard_pity / 10):
                up_break = False
                for _ in xrange(10):
                    total_pull_count += 1
                    star6_pull_count += 1
                    cur_rate = random.random()
                    is_up, star6_rate = self.get_star6_rate(star6_pull_count, total_pull_count)
                    # 抽到up也要抽完这次10连，然后停手
                    if cur_rate < star6_rate:
                        star6_pull_count = 0
                        if is_up:
                            up_break = True

                if up_break:
                    all_pull_count.append(total_pull_count)
                    break

        return all_pull_count

    def get_star6_rate(self, star6_pull_count, total_pull_count):
        '''
        star6_pull_count 连续多少次没出6星
        total_pull_count 当前池子总抽数

        return 是否up, 6星概率
        '''
        # 120抽大保底
        if total_pull_count == self.hard_pity:
            return True, 1.0

        # 小于65抽正常计算
        if star6_pull_count <= self.pity_threshold:
            return self.is_up(), self.base_rate
        # 66~79抽概率递增
        elif star6_pull_count < self.soft_pity:
            return self.is_up(), self.base_rate + (star6_pull_count - self.pity_threshold) * self.rate_increase
        # 80抽小保底
        else:
            return self.is_up(), 1.0

    def is_up(self):
        return random.random() < self.up_rate

def calculate_confidence_intervals(data, confidence_intervals):
    """计算指定百分位数的置信区间"""
    data_sorted = sorted(data)
    n = len(data_sorted)

    percentiles = confidence_intervals
    results = {}

    for p in percentiles:
        # 计算百分位数位置
        index = (p / 100.0) * (n - 1)
        if index.is_integer():
            results[p] = data_sorted[int(index)]
        else:
            # 线性插值
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            results[p] = data_sorted[lower_index] * (1 - weight) + data_sorted[upper_index] * weight

    return results

def print_result(results_data, confidence_intervals=None):
    confidence_intervals = confidence_intervals or [10,25,50,75,90]
    # 计算平均值
    average = 1.0 * sum(results_data) / len(results_data)

    # 计算方差和标准差
    variance = sum((x - average) ** 2 for x in results_data) / len(results_data)
    std_deviation = variance ** 0.5

    # 计算置信区间
    confidence_interval_results = calculate_confidence_intervals(results_data, confidence_intervals)

    print("===============================================================")
    print("抽卡统计结果:")
    print("总模拟次数: %d" % len(results_data))
    print("平均抽数: %.2f" % average)
    print("方差: %.2f" % variance)
    print("标准差: %.2f" % std_deviation)
    print("\n置信区间:")
    for _intervals in confidence_intervals:
        print("%d%% 分位数: %.1f 抽" % (_intervals, confidence_interval_results[_intervals]))
    print("===============================================================")


def print_calculate_loss(single_results, ten_results, confidence_intervals=None):
    """
    计算十连相对于单抽的亏损，提供更详细的分析数据
    """
    # 平均抽卡次数对比
    avg_single = 1.0 * sum(single_results) / len(single_results)
    avg_ten = 1.0 * sum(ten_results) / len(ten_results)

    # 亏损率计算
    loss_rate = (avg_ten - avg_single) / avg_single * 100

    # 绝对亏损值
    absolute_loss = avg_ten - avg_single

    # 计算绝对亏损的置信区间
    # 通过Bootstrap方法估算置信区间
    bootstrap_samples = 1000
    absolute_losses = []

    for _ in range(bootstrap_samples):
        # 有放回采样
        bootstrap_single = [random.choice(single_results) for _ in range(len(single_results))]
        bootstrap_ten = [random.choice(ten_results) for _ in range(len(ten_results))]

        boot_avg_single = 1.0 * sum(bootstrap_single) / len(bootstrap_single)
        boot_avg_ten = 1.0 * sum(bootstrap_ten) / len(bootstrap_ten)

        boot_absolute_loss = boot_avg_ten - boot_avg_single
        absolute_losses.append(boot_absolute_loss)

    # 计算绝对亏损的置信区间
    absolute_losses.sort()
    # 指定的置信区间百分位数
    confidence_intervals = confidence_intervals or [10, 25, 50, 75, 90]
    absolute_confidence_results = {}

    for p in confidence_intervals:
        index = int((p / 100.0) * (len(absolute_losses) - 1))
        absolute_confidence_results[p] = absolute_losses[index]

    print("===============================================================")
    print("亏损对比分析:")
    print("单抽平均抽数: %.2f" % avg_single)
    print("十连平均抽数: %.2f" % avg_ten)
    print("绝对亏损(多消耗的平均抽数): %.2f" % absolute_loss)
    print("相对亏损率: %.2f%%" % loss_rate)

    print("\n绝对亏损置信区间:")
    for p in confidence_intervals:
        print("%d%% 分位数: %.2f 抽" % (p, absolute_confidence_results[p]))
    print("===============================================================")





if __name__ == '__main__':
    pool = POOL(draw_count=1000000)
    # 单抽
    single_results_data = pool.pull_single()
    print_result(single_results_data, [10,20,30,40,50,60,70,80,90])

    # 十连
    ten_results_data = pool.pull_ten()
    print_result(ten_results_data, [10,20,30,40,50,60,70,80,90])

    # 计算亏损
    print_calculate_loss(single_results_data, ten_results_data, [10, 20, 30, 40, 50, 60, 70, 80, 90])
