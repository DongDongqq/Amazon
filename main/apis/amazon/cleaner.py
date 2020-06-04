import json
import traceback
from lxml import etree
import re
import copy
from urllib.parse import unquote

import time


class AmazonCleaner:
    def goodsList(self, data):
        """
        商品列表清洗
        :param data:
        :return:
        """
        res = {}
        tree = etree.HTML(data)

        res_data = []
        items = tree.xpath('//div[contains(@class,"s-result-list")]/div[@data-asin]')

        if len(items) == 0:
            res['code'] = 201
            res['msg'] = '列表为空'
            return res

        try:
            for item in items:
                item_data = {
                    'itemId': self.goodsListFieldCleaner(item, 'itemId'),
                    'img': self.goodsListFieldCleaner(item, 'img'),
                    'badge': self.goodsListFieldCleaner(item, 'badge'),
                    'sponsored': self.goodsListFieldCleaner(item, 'sponsored'),
                    'title': self.goodsListFieldCleaner(item, 'title'),
                    'by': self.goodsListFieldCleaner(item, 'by'),
                    'url': self.goodsListFieldCleaner(item, 'url'),
                    'rateInfo': self.goodsListFieldCleaner(item, 'rateInfo'),
                    'priceInfo': self.goodsListFieldCleaner(item, 'priceInfo'),
                    'shipping': self.goodsListFieldCleaner(item, 'shipping'),
                    'stockInfo': self.goodsListFieldCleaner(item, 'stockInfo'),
                    'moreBuyingChoices': self.goodsListFieldCleaner(item, 'moreBuyingChoices'),
                    'subscribeSave': self.goodsListFieldCleaner(item, 'subscribeSave'),
                    'couponSave': self.goodsListFieldCleaner(item, 'couponSave'),
                    'speciesType': self.goodsListFieldCleaner(item, 'speciesType'),
                    'otherSpecies': self.goodsListFieldCleaner(item, 'otherSpecies'),
                    'otherVersions': self.goodsListFieldCleaner(item, 'otherVersions'),
                }

                res_data.append(item_data)

            res['code'] = 200
            res['msg'] = 'true'
            res['data'] = res_data

        except:
            res['code'] = 401
            res['msg'] = str(traceback.format_exc())

        return res

    def goodsListFieldCleaner(self, item, type, clean_for_special=False):
        '''
        商品列表字段清洗
        :param item: 数据项
        :param type: 数据类型
        :return:
        '''
        # 拷贝节点对象，不然如果中途对节点做了修改，可能会出问题，比如价格取不到取更多选择中的价格时
        item = copy.copy(item)
        result = ''
        if type == 'itemId':
            result = item.xpath('./@data-asin')
            result = result[0] if result else ''

        elif type == 'img':
            result = item.xpath('.//img[@class="s-image"]/@src')
            result = result[0] if result else ''

        elif type == 'badge':
            data_asin = item.xpath('./@data-asin')[0]
            result = item.xpath(f'.//div[@class="sg-row"][1]//span[@id="{data_asin}-label"]//span/text()')
            result = ''.join([i.strip('\n').strip() for i in result])

        elif type == 'sponsored':
            # result = item.xpath(
            #     './/div[@class="a-section a-spacing-none a-spacing-top-small"]/div[@class="a-row a-spacing-micro"]/span[@class="a-size-base a-color-secondary"]/text()')
            result = item.xpath(
                './/div[contains(@class, "a-section a-spacing-none")]/div[@class="a-row a-spacing-micro"]/span[@class="a-size-base a-color-secondary"]/text()')
            result = result[0] if result else ''

        elif type == 'title':
            result = item.xpath('.//span[contains(@class, "a-color-base a-text-normal")]/text()')
            result = result[0] if result else ''

        elif type == 'by':
            result = item.xpath('string(.//h2/following-sibling::div[@class="a-row a-size-base a-color-secondary"])')
            result = re.sub(' +', ' ', result.replace('\n', '').strip())

        elif type == 'url':
            result = item.xpath('.//h2/a[@class="a-link-normal a-text-normal"]/@href')
            if result:
                result = 'https://www.amazon.com' + result[0]
            else:
                result = ''

        elif type == 'rateInfo':
            rating = item.xpath('.//span[@class="a-icon-alt"]/text()')
            rate_num = item.xpath('.//a[@class="a-link-normal"]/span[@class="a-size-base"]/text()')
            rate_link = item.xpath('.//div[@class="a-row a-size-small"]//a[@class="a-link-normal"]/@href')
            itemId = item.xpath('./@data-asin')[0] if item.xpath('./@data-asin') else ''

            result = {
                'rating': rating[0] if rating else '',
                'rateNum': rate_num[0] if rate_num else '',
                'rateLink': f'https://www.amazon.com/dp/{itemId}/{rate_link[0]}' if rate_link else ''
            }

        elif type == 'priceInfo':
            if not clean_for_special:
                new_item = item.xpath('.//div[@class="a-section a-spacing-none a-spacing-top-small"]')
                if new_item:
                    item = new_item[0]
                else:
                    return result

            result = item.xpath(
                './/a[@class="a-size-base a-link-normal s-no-hover a-text-normal"]//span[@class="a-offscreen"]/text()')
            price_range_tag = item.xpath('.//span[@class="a-price-dash"]/text()')
            if price_range_tag:
                result = {'current': '-'.join(result)}
            else:
                keys = ['current', 'original']
                result = dict(zip(keys, result))
                # 单价处理
                unit_price = item.xpath('.//span[@class="a-price"]/following-sibling::span/text()')
                if unit_price:
                    result['byUnit'] = unit_price[0]

            # 若价格为空，则取'更多购买选择'中的价格
            if not result:
                more_buying_choices = self.goodsListFieldCleaner(item, 'moreBuyingChoices')
                if more_buying_choices:
                    choice_info = more_buying_choices['title']
                    current_price = re.search('(US\$[\d.,]*) ', choice_info)
                    result['current'] = current_price.group(1) if current_price else ''

        elif type == 'shipping':
            result = item.xpath('.//span[@class="a-size-small a-color-secondary"]/text()')
            result = result[0] if result else ''

        elif type == 'stockInfo':
            if not clean_for_special:
                new_item = item.xpath(
                    './/div[@class="a-section a-spacing-none a-spacing-top-micro"]/div[@class="a-row a-size-base a-color-secondary"]/span/@aria-label')
                if not new_item:
                    return result

            result = item.xpath('.//div[@class="a-row a-size-base a-color-secondary"]/span/@aria-label')
            result = result[0].strip() if result else ''

        elif type == 'moreBuyingChoices':
            if not clean_for_special:
                new_item = item.xpath('.//div[@class="a-section a-spacing-none a-spacing-top-mini"]')
                if new_item:
                    item = new_item[0]
                else:
                    return result

            more_buying_choices = item.xpath(
                './/div[@class="a-row a-size-base a-color-secondary"]/span[@class="a-size-base a-color-secondary"]/..')
            title_root = ''
            if more_buying_choices:
                node_title_root = more_buying_choices[0].xpath('.//span[@class="a-size-base a-color-secondary"]')
                if node_title_root:
                    title_root = node_title_root[0].xpath('string(.)')
                    more_buying_choices[0].remove(node_title_root[0])

                title = more_buying_choices[0].xpath('string(.)')
                link = more_buying_choices[0].xpath('.//a[@class="a-link-normal"]/@href')
                result = {
                    'title_root': title_root.replace('\n', '').strip(),
                    'title': re.sub(' +', ' ', title.replace('\n', '').strip()),
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'subscribeSave':
            result = item.xpath(
                './/div[@class="a-section a-spacing-none a-spacing-top-small"]/div[@class="a-row a-size-small a-color-secondary"]/span/text()')
            result = [i for i in result if i.strip('\n').strip() != '']
            result = result[0] if result else ''

        elif type == 'couponSave':
            result = item.xpath(
                './/div[@class="a-section a-spacing-none a-spacing-top-small"]//span[@class="s-coupon-unclipped "]/span/text()')
            result = ' '.join([i.strip('\n').strip() for i in result])

        elif type == 'speciesType':
            result = item.xpath('string(.//a[@class="a-size-base a-link-normal a-text-bold"])')
            result = result.replace('\n', '').strip()

        elif type == 'otherSpecies':
            otherSpecies = []
            results = item.xpath('//div[@class="a-row"]/div[@class="a-row a-spacing-mini"]')
            for result in results:
                species_type = self.goodsListFieldCleaner(result, 'speciesType')
                price_info = self.goodsListFieldCleaner(result, 'priceInfo', clean_for_special=True),
                stock_info = self.goodsListFieldCleaner(result, 'stockInfo', clean_for_special=True),
                more_buying_choices = self.goodsListFieldCleaner(result, 'moreBuyingChoices', clean_for_special=True),

                species = {
                    'speciesType': species_type,
                    'priceInfo': price_info,
                    'stockInfo': stock_info[0] if stock_info else '',
                    'moreBuyingChoices': more_buying_choices[0] if more_buying_choices else '',
                }

                otherSpecies.append(species)

            result = otherSpecies

        elif type == 'otherVersions':
            other_versions = []
            versions = item.xpath(
                './/div[@class="a-row a-spacing-top-micro a-size-small a-color-base"]/a[@class="a-size-small a-link-normal"]')
            for version in versions:
                title = version.xpath('./text()')
                link = version.xpath('./@href')
                other_versions.append({
                    'title': title[0].replace('\n', '').strip() if title else '',
                    'link': f'https://www.amazon.com{link[0]}' if link else '',
                })

            result = other_versions

        return result

    def goodsDetail(self, data, itemId):
        '''
        商品详情清洗
        :param data:
        :return:
        '''
        res = {}
        tree = etree.HTML(data)
        res_data = {}

        not_found_tag1 = tree.xpath('//img[@src="https://images-na.ssl-images-amazon.com/images/G/01/error/title._TTD_.png"]')
        not_found_tag2 = tree.xpath('//a[@href="/ref=cs_404_link"]')

        refuse_info = tree.xpath('//p[@class="a-last"]//text()')
        if refuse_info and refuse_info[0] == "Sorry, we just need to make sure you're not a robot. For best results, please make sure your browser is accepting cookies.":
            res['code'] = 401
            res['msg'] = '请求出错'
            return res

        if not_found_tag1 or not_found_tag2:
            res['code'] = 201
            res['msg'] = '商品信息不存在'
            return res

        cleaner = self.getGoodsDetailFieldCleaner(tree)

        try:
            res_data['title'] = cleaner(tree, 'title')
            res_data['imgs'] = cleaner(tree, 'imgs', page_source=data)
            res_data['by'] = cleaner(tree, 'by')
            res_data['rateInfo'] = cleaner(tree, 'rateInfo', itemId=itemId)
            res_data['QAInfo'] = cleaner(tree, 'QAInfo')
            res_data['skuProps'] = cleaner(tree, 'skuProps')
            res_data['features'] = cleaner(tree, 'features', page_source=data)
            res_data['comparison'] = cleaner(tree, 'comparison', itemId=itemId, page_source=data)
            res_data['olpFeature'] = cleaner(tree, 'olpFeature')
            res_data['priceInfo'] = cleaner(tree, 'priceInfo')
            res_data['deliveryMessage'] = cleaner(tree, 'deliveryMessage')
            res_data['stockInfo'] = cleaner(tree, 'stockInfo')
            res_data['merchantInfo'] = cleaner(tree, 'merchantInfo')
            res_data['productDescription'] = cleaner(tree, 'productDescription',page_source=data)
            res_data['productDetails'] = cleaner(tree, 'productDetails', page_source=data)

            res['code'] = 200
            res['msg'] = 'true'
            res['data'] = res_data

        except:
            print(traceback.format_exc())
            res['code'] = 401
            res['msg'] = str(traceback.format_exc())

        return res

    def getGoodsDetailFieldCleaner(self, item):
        '''
        获取商品详情清洗器
        有些类别的商品的页面格式差异与正常格式差异较大
        所以根据商品所属类别采用不同的解析器
        '''
        cleaner = self.goodsDetailFieldCleaner

        goods_type = item.xpath('//div[@id="dp"]/@class')
        goods_type = goods_type[0] if goods_type else ''

        if 'book' in goods_type or 'home' in goods_type:
            cleaner = self.goodsDetailFieldCleaner2
        return cleaner

    def goodsDetailFieldCleaner(self, item, type, page_source=None, itemId=None):
        '''
        商品详情字段清洗器(通用商品)
        '''
        result = ''


        if type == 'title':
            result = item.xpath('string(.//*[@id="title"])')
            result = re.sub(' +', ' ', result.replace('\n', '')).strip()

        elif type == 'imgs':
            # 用正则匹配js代码中的图片
            try:
                imgs = re.search(r'{[\s\S]*?\'colorImages\': { \'initial\': (.*)', page_source)
                result = json.loads(imgs.group(1).rstrip(',').rstrip('}'))
            except:
                result = ''

        elif type == 'by':
            result = item.xpath('//a[@id="bylineInfo"]')
            if result:
                title = result[0].xpath('./text()')
                link = result[0].xpath('./@href')
                result = {
                    'title': title[0] if title else '',
                    'link': 'https://www.amazon.com' + link[0] if link else ''
                }

        elif type == 'rateInfo':
            result = item.xpath('//div[@id="averageCustomerReviews"]')
            if result:
                rating = result[0].xpath('.//span[@class="a-icon-alt"]/text()')
                rate_num = result[0].xpath('.//span[@id="acrCustomerReviewText"]/text()')
                rate_link = result[0].xpath('//a[@id="acrCustomerReviewLink"]/@href')

                result = {
                    'rating': rating[0] if rating else '',
                    'rateNum': rate_num[0] if rate_num else '',
                    'rateLink': f'https://www.amazon.com/dp/{itemId}/{rate_link[0]}' if rate_link else ''
                }

        elif type == 'QAInfo':
            result = item.xpath('//a[@id="askATFLink"]')
            if result:
                qa_num = result[0].xpath('./span/text()')
                qa_link = result[0].xpath('./@href')
                result = {
                    'QANum': ''.join(qa_num).strip('\n').strip(),
                    'QALink': f'https://www.amazon.com{qa_link[0]}' if qa_link else ''
                }

        elif type == 'skuProps':
            sku_props = []
            sku_color = self.getSkuColor(item) or self.getSkuColor2(item)
            if sku_color:
                sku_props.append(sku_color)

            sku_size = self.getSkuSize(item) or self.getSkuSize2(item)
            if sku_size:
                sku_props.append(sku_size)

            sku_style = self.getSkuStyle(item) or self.getSkuStyle2(item)
            if sku_style:
                sku_props.append(sku_style)

            if sku_props:
                result = sku_props

        elif type == 'features':
            result = []
            features = item.xpath('//div[@id="featurebullets_feature_div"]//ul/li')
            for feature in features:
                feature_text = feature.xpath('./span[@class="a-list-item"]/text()')
                feature_text = feature_text[0].replace('\n', '').replace('\t', '').strip()
                if feature_text:
                    result.append(feature_text)

        elif type == 'comparison':
            r = re.search(
                '<div class="a-section a-spacing-small a-spacing-top-small HLCXComparisonJumplinkContent aok-hidden">(.*?)</div>',
                page_source, re.S)
            if r:
                comparison_item = etree.HTML(r.group(1))
                if len(comparison_item):
                    title = comparison_item[0].xpath(
                        './/a[@class="a-link-normal HLCXComparisonJumplinkLink"]/span/text()')
                    link = comparison_item[0].xpath('.//a[@class="a-link-normal HLCXComparisonJumplinkLink"]/@href')

                    result = {
                        'title': title[0] if title else '',
                        'link': f'https://www.amazon.com/dp/{itemId}/{link[0]}' if link else ''
                    }

        elif type == 'olpFeature':
            olp_feature = item.xpath('//div[@id="olp_feature_div"]')
            if olp_feature:
                title = olp_feature[0].xpath('string(.//span[1]/a)')
                link = olp_feature[0].xpath('.//span[1]/a/@href')

                result = {
                    'title': title if title else '',
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'priceInfo':
            price_info = item.xpath('//div[@id="price"]')
            if price_info:
                original = price_info[0].xpath('//span[@class="priceBlockStrikePriceString a-text-strike"]/text()')
                current = price_info[0].xpath('//span[@id="priceblock_ourprice"]/text()')
                if not current:
                    current =  price_info[0].xpath('//span[@id="priceblock_saleprice"]/text()')
                save = price_info[0].xpath(
                    '//td[@class="a-span12 a-color-price a-size-base priceBlockSavingsString"]/text()')
                delivery = price_info[0].xpath('//span[@id="ourprice_shippingmessage"]/span/text()')
                delivery_detail = item.xpath('//div[@id="a-popover-agShipMsgPopover"]')
                if delivery_detail:
                    price = delivery_detail[0].xpath('.//tr[1]/td[3]/span/text()')
                    delivery_fee = delivery_detail[0].xpath('.//tr[2]/td[3]/span/text()')
                    tax = delivery_detail[0].xpath('.//tr[3]/td[3]/span/text()')
                    total = delivery_detail[0].xpath('.//tr[5]/td[3]/span/text()')

                    delivery_detail = {
                        'price': price[0].strip() if price else '',
                        'deliveryFee': delivery_fee[0].strip() if delivery_fee else '',
                        'tax': tax[0].strip() if tax else '',
                        'total': total[0].strip() if total else ''
                    }
                else:
                    delivery_detail = ''

                if delivery:
                    delivery = {
                        'title': delivery[0].replace('\n', '').strip() if delivery else '',
                        'detail': delivery_detail
                    }
                else:
                    delivery = ''

                result = {
                    'original': original[0].strip() if original else '',
                    'current': current[0] if current else '',
                    'save': save[0] if save else '',
                    'delivery': delivery,
                }

        elif type == 'deliveryMessage':
            delivery_message = item.xpath('//div[@id="delivery-message"]')
            if delivery_message:
                no_need_node = delivery_message[0].xpath('./a[@target="AmazonHelp"]')
                if no_need_node:
                    delivery_message[0].remove(no_need_node[0])

                result = delivery_message[0].xpath('string(.)').replace('\n', '').strip()

        elif type == 'stockInfo':
            stock_info = item.xpath('string(//*[@id="availability"])')
            result = re.sub(' +', ' ', stock_info.replace('\n', '').strip())

        elif type == 'merchantInfo':
            merchant_info = item.xpath('//div[@id="merchant-info"]')
            if merchant_info:
                no_need_node1 = merchant_info[0].xpath('.//div[@id="a-popover-seller-popover-body"]')
                if no_need_node1:
                    merchant_info[0].remove(no_need_node1[0])

                no_need_node2 = merchant_info[0].xpath('.//script')
                if no_need_node2:
                    merchant_info[0].remove(no_need_node2[0])

                title = merchant_info[0].xpath('string(.)').replace('\n', '').strip()
                link = merchant_info[0].xpath('.//a[@id="sellerProfileTriggerId"]/@href')

                result = {
                    'title': title,
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'productDescription':
            r = re.search(r'<div id="productDescription_feature_div" data-feature-name="productDescription" data-template-name="productDescription" class="a-row feature">(.*)</div>',
                page_source,re.S)

            if r:
                item = etree.HTML(r.group(1))
                desc = item.xpath('//*[@id="productDescription"]/p//text()')
                result = ''.join(desc).replace('\n', '').strip() if desc else ''
            if not result:
                result = {}
                r = re.search(r'<div id="aplus3p_feature_div" class="feature" data-feature-name="aplus3p">(.*)</div>',page_source,re.S)
                if r:
                    item = etree.HTML(r.group(1))
                    img_url = item.xpath('//*[@id="aplus"]/div//img//@src')
                    if img_url:
                        img_url = [i for i in img_url if i != "https://images-na.ssl-images-amazon.com/images/G/01/x-locale/common/grey-pixel.gif" ]
                    descriptionText = item.xpath('//*[@id="aplus"]/div//p//text()')
                    descriptionText = ''.join(descriptionText).replace('\n', '').strip()
                    result['descriptionImgs'] = img_url
                    result['descriptionText'] = descriptionText


        elif type == 'productDetails':
            r = re.search(r'<div id="prodDetails" .*?>(.*)</div>', page_source, re.S) or re.search(
                r'<div id="technicalSpecifications_feature_div" .*?>(.*)</div>', page_source, re.S)
            if r:
                result = []
                item = etree.HTML(r.group(1))
                details = item.xpath('//table[contains(@class,"a-keyvalue")]/tr')
                for detail in details:
                    name = detail.xpath('string(./th)')
                    value = detail.xpath('string(./td)')

                    if detail.xpath('./td/div[@id="averageCustomerReviews"]'):
                        value = ''.join(detail.xpath('./td/text()'))

                    result.append({
                        'name': name.replace('\n', '').strip(),
                        'value': re.sub(' +', ' ', value.replace('\n', '').strip())
                    })
            else:
                r = re.search(r'<div id="detailBullets" class="feature" data-feature-name="detailBullets">(.*)</div>', page_source,re.S)
                if r:
                    result = []
                    item = etree.HTML(r.group(1))
                    details= item.xpath('//div[@id="detailBullets_feature_div"]//li')
                    for detail in details:
                        name = detail.xpath('string(.//span[@class="a-text-bold"])').replace('\n', '').strip()
                        value_node = detail.xpath('string(.//span[@class="a-list-item"]/span[2])').replace('\n', '').strip()
                        a_href = detail.xpath('.//span[@class="a-list-item"]//a//@href')
                        if a_href:
                            value_node = value_node+a_href[0]
                        if name or value_node:
                            result.append({
                                'name': name,
                                'value': value_node
                            })
                    salesRanks = item.xpath('//li[@id="SalesRank"]')
                    if salesRanks:
                        salesRank = salesRanks[0]
                        name = salesRank.xpath('string(./b[1])').replace('\n', '').strip()
                        value = salesRank.xpath('string()').replace('\n', '').strip()
                        value=re.sub(r' .zg_hrsr { margin: 0; padding: 0; list-style-type: none; }.zg_hrsr_item { margin: 0 0 0 10px; }.zg_hrsr_rank { display: inline-block; width: 80px; text-align: right; }| ','',value)
                        all_rank_name = salesRank.xpath('string(./a[1])').replace('\n', '').strip()
                        all_rank_link = 'https://www.amazon.com'+salesRank.xpath('.//a[1]//@href')[0]

                        result.append({
                            'name': name,
                            'value': value.replace(name,'')
                        })
                        result.append({
                            'name': all_rank_name,
                            'value': all_rank_link
                        })



            # 若以上解析无法取得数据，则使用下一种解析方式
            if not result:
                result = []
                details = item.xpath('//div[@id="prodDetails"]//table/tbody/tr')

                for detail in details:
                    name = detail.xpath('string(./td[1])')
                    value_node = detail.xpath('./td[2]')
                    if value_node:
                        no_need_node = value_node[0].xpath('./style')
                        if no_need_node:
                            value_node[0].remove(no_need_node[0])

                    value = detail.xpath('string(./td[2])')

                    name = name.replace('\n', '').strip()
                    value = re.sub(' +', ' ', value.replace('\n', '').strip())
                    if name or value:
                        result.append({
                            'name': name,
                            'value': value
                        })

            if not result:
                result = []
                details = item.xpath('//div[@id="detail-bullets"]//table//div[@class="content"]/ul/li')
                for detail in details:
                    name = detail.xpath('string(.//b)')

                    no_need_node = detail.xpath('./style')
                    if no_need_node:
                        detail.remove(no_need_node[0])

                    value = detail.xpath('string(.)').replace(name, '')
                    result.append({
                        'name': name.replace('\n', '').strip().rstrip(':').rstrip('：'),
                        'value': re.sub(' +', ' ', value.replace('\n', '').strip())
                    })

            if not result:
                result = []


        return result

    def goodsDetailFieldCleaner2(self, item, type, page_source=None, itemId=None):
        '''
        商品详情字段清洗器(book商品...)
        '''
        result = ''
        if type == 'title':
            result = item.xpath('string(.//*[@id="title"])')
            result = re.sub(' +', ' ', result.replace('\n', '')).strip()

        elif type == 'imgs':
            result = item.xpath('//div[@id="leftCol"]//img/@src')
            result = result[0] if result else ''

        elif type == 'by':
            result = item.xpath('//div[@id="bylineInfo"]')
            if result:
                title = result[0].xpath('.//a[@class="a-link-normal contributorNameID"]/text()')
                link = result[0].xpath('.//a[@class="a-link-normal contributorNameID"]/@href')

                result = {
                    'title': title[0] if title else '',
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'rateInfo':
            result = item.xpath('//div[@id="averageCustomerReviews"]')
            if result:
                rating = result[0].xpath('.//span[@class="a-icon-alt"]/text()')
                rate_num = result[0].xpath('.//span[@id="acrCustomerReviewText"]/text()')
                rate_link = result[0].xpath('//a[@id="acrCustomerReviewLink"]/@href')

                result = {
                    'rating': rating[0] if rating else '',
                    'rateNum': rate_num[0] if rate_num else '',
                    'rateLink': f'https://www.amazon.com/dp/{itemId}/{rate_link[0]}' if rate_link else ''
                }

        elif type == 'QAInfo':
            result = item.xpath('//a[@id="askATFLink"]')
            if result:
                qa_num = result[0].xpath('./span/text()')
                qa_link = result[0].xpath('./@href')

                result = {
                    'QANum': ''.join(qa_num).strip('\n').strip(),
                    'QALink': f'https://www.amazon.com{qa_link[0]}' if qa_link else ''
                }

        elif type == 'skuProps':
            sku_props = []
            sku_color = self.getSkuColor(item)
            if sku_color:
                sku_props.append(sku_color)
            sku_size = self.getSkuSize(item)
            if sku_size:
                sku_props.append(sku_size)
            sku_style = self.getSkuStyle(item)
            if sku_style:
                sku_props.append(sku_style)


            sku_formats = self.getSkuFormats(item)
            if sku_formats:
                sku_props.append(sku_formats)
            result = sku_props

        elif type == 'features':
            r = re.search(
                r'<div id="bookDescription_feature_div" class="feature" data-feature-name="bookDescription">(.*)</div>',
                page_source, re.S)

            if r:
                item = etree.HTML(r.group(1))
                desc = item.xpath('//noscript/div/*')
                for d in desc:
                    result += str(etree.tostring(d, encoding="utf-8"), 'utf-8') if desc else ''

        elif type == 'comparison':
            r = re.search(
                '<div class="a-section a-spacing-small a-spacing-top-small HLCXComparisonJumplinkContent aok-hidden">(.*?)</div>',
                page_source, re.S)
            if r:
                comparison_item = etree.HTML(r.group(1))
                if len(comparison_item):
                    title = comparison_item[0].xpath(
                        './/a[@class="a-link-normal HLCXComparisonJumplinkLink"]/span/text()')
                    link = comparison_item[0].xpath('.//a[@class="a-link-normal HLCXComparisonJumplinkLink"]/@href')

                    result = {
                        'title': title[0] if title else '',
                        'link': f'https://www.amazon.com/dp/{itemId}/{link[0]}' if link else ''
                    }

        elif type == 'olpFeature':
            olp_feature = item.xpath('//div[@id="olp_feature_div"]')
            if olp_feature:
                title = olp_feature[0].xpath('string(.//span[1]/a)')
                link = olp_feature[0].xpath('.//span[1]/a/@href')
                result = {
                    'title': title if title else '',
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'priceInfo':
            price_info = item.xpath('//div[@id="buybox"]')
            if price_info:
                original = price_info[0].xpath('.//span[@class="a-list-item"]/span[@class="a-color-secondary a-text-strike"]/text()')
                current = price_info[0].xpath('.//span[contains(@class, "a-color-price")]/text()')
                save = price_info[0].xpath('.//span[@class="a-list-item"]/span[@class="a-size-base a-color-secondary"]/text()')
                delivery = ''
                if original or current or save or delivery:
                    result = {
                        'original': original[0].strip() if original else '',
                        'current': current[0].replace('\n', '').strip() if current else '',
                        'save': save[0].replace('\n', '').strip() if save else '',
                        'delivery': delivery
                    }

        elif type == 'deliveryMessage':
            delivery_message = item.xpath('//div[@id="delivery-message"]')
            if delivery_message:
                no_need_node = delivery_message[0].xpath('./a[@target="AmazonHelp"]')
                if no_need_node:
                    delivery_message[0].remove(no_need_node[0])

                result = delivery_message[0].xpath('string(.)').replace('\n', '').strip()

        elif type == 'stockInfo':
            stock_info = item.xpath('string(//div[@id="availability"])')
            result = re.sub(' +', ' ', stock_info.replace('\n', '').strip())

        elif type == 'merchantInfo':
            merchant_info = item.xpath('//div[@id="merchant-info"]')
            if merchant_info:
                no_need_node1 = merchant_info[0].xpath('.//div[@id="a-popover-seller-popover-body"]')
                if no_need_node1:
                    merchant_info[0].remove(no_need_node1[0])

                no_need_node2 = merchant_info[0].xpath('.//script')
                if no_need_node2:
                    merchant_info[0].remove(no_need_node2[0])

                title = merchant_info[0].xpath('string(.)').replace('\n', '').strip()
                link = merchant_info[0].xpath('.//a[@id="sellerProfileTriggerId"]/@href')
                result = {
                    'title': title,
                    'link': f'https://www.amazon.com{link[0]}' if link else ''
                }

        elif type == 'productDescription':
            r = re.search(
                r'<div id="productDescription_feature_div" data-feature-name="productDescription" data-template-name="productDescription" class="a-row feature">(.*)</div>',
                page_source, re.S)
            '''
            if r:
                item = etree.HTML(r.group(1))
                # 显示纯文本
                # desc = item.xpath('string(//div[@id="productDescription"])')
                # result = desc.strip()

                # 显示节点+文本
                desc = item.xpath('//div[@id="productDescription"]//*')
                for d in desc:
                    result += str(etree.tostring(d, encoding="utf-8"), 'utf-8') if desc else ''

            if not result:
                r = re.search('obj.initialize = .*var iframeContent = "(.*)";',page_source,re.S)
                if r:
                    result = unquote(r.group(1))
            '''
            if r:
                item = etree.HTML(r.group(1))
                desc = item.xpath('//*[@id="productDescription"]/p//text()')
                result = ''.join(desc).replace('\n', '').strip() if desc else ''
            if not result:
                result = {}
                r = re.search(r'<div id="aplus3p_feature_div" class="feature" data-feature-name="aplus3p">(.*)</div>',page_source,re.S)
                if r:
                    item = etree.HTML(r.group(1))
                    img_url = item.xpath('//*[@id="aplus"]/div//img//@src')
                    if img_url:
                        img_url = [i for i in img_url if i != "https://images-na.ssl-images-amazon.com/images/G/01/x-locale/common/grey-pixel.gif" ]
                    descriptionText = item.xpath('//*[@id="aplus"]/div//p//text()')
                    descriptionText = ''.join(descriptionText).replace('\n', '').strip()
                    result['descriptionImgs'] = img_url
                    result['descriptionText'] = descriptionText


        elif type == 'productDetails':
            r = re.search(r'<div id="prodDetails" .*?>(.*)</div>', page_source, re.S) or re.search(
                r'<div id="technicalSpecifications_feature_div" .*?>(.*)</div>', page_source, re.S)

            if r:
                result = []
                item = etree.HTML(r.group(1))
                details = item.xpath('//table[contains(@class,"a-keyvalue")]/tr')
                for detail in details:
                    name = detail.xpath('string(./th)')
                    value = detail.xpath('string(./td)')
                    if detail.xpath('./td/div[@id="averageCustomerReviews"]'):
                        value = ''.join(detail.xpath('./td/text()'))
                    result.append({
                        'name': name.replace('\n', '').strip(),
                        'value': re.sub(' +', ' ', value.replace('\n', '').strip())
                    })

            # 若以上解析无法取得数据，则使用下一种解析方式
            if not result:
                result = []
                details = item.xpath('//div[@id="prodDetails"]//table/tbody/tr')
                for detail in details:
                    name = detail.xpath('string(./td[1])')
                    value_node = detail.xpath('./td[2]')
                    if value_node:
                        no_need_node = value_node[0].xpath('./style')
                        if no_need_node:
                            value_node[0].remove(no_need_node[0])
                    value = detail.xpath('string(./td[2])')
                    name = name.replace('\n', '').strip()
                    value = re.sub(' +', ' ', value.replace('\n', '').strip())
                    if name or value:
                        result.append({
                            'name': name,
                            'value': value
                        })
            if not result:
                result = []
                details = item.xpath('//div[@id="detail-bullets"]//table//div[@class="content"]/ul/li')
                for detail in details:
                    name = detail.xpath('string(.//b)')
                    no_need_node = detail.xpath('./style')
                    if no_need_node:
                        detail.remove(no_need_node[0])
                    value = detail.xpath('string(.)').replace(name, '')
                    result.append({
                        'name': name.replace('\n', '').strip().rstrip(':').rstrip('：'),
                        'value': re.sub(' +', ' ', value.replace('\n', '').strip())
                    })

        return result

    def getSkuColor(self, item):
        sku_prop = {}
        sku_color = item.xpath('//div[@id="variation_color_name"]')
        if sku_color:
            sku_prop['name'] = 'color'
            current_color = sku_color[0].xpath('.//span[@class="selection"]/text()')
            sku_items = []
            colors = sku_color[0].xpath('./ul/li')
            if not colors:
                sku_items.append({'title': current_color[0] if current_color else ''})
            else:
                for color in colors:
                    itemId = color.xpath('./@data-defaultasin')
                    img = color.xpath('.//img/@src')
                    title = color.xpath('.//img/@alt')
                    price = color.xpath('.//span[@class="a-size-mini twisterSwatchPrice"]/text()')
                    sku_items.append(
                        {
                            'itemId': itemId[0] if itemId else '',
                            'img': img[0] if img else '',
                            'title': title[0] if title else '',
                            'price': price[0].strip() if price else ''
                        }
                    )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuColor2(self,item):
        '''
        针对第二种页面样式的颜色解析
        '''
        sku_prop = {}
        sku_color = item.xpath('//div[@id="shelf-color_name"]')
        if sku_color:
            sku_prop['name'] = 'color'

            current_color = sku_color[0].xpath('.//div[@id="shelf-label-color_name"]//span[@class="shelf-label-variant-name"]/text()')
            sku_items = []
            colors = sku_color[0].xpath('./div[@id="shelfSwatchSection-color_name"]//div[@data-dp-url]')
            if not colors:
                sku_items.append({'title': current_color[0] if current_color else ''})
            else:
                for color in colors:
                    img = color.xpath('.//img[@class="twisterShelf_swatch_img"]/@src')
                    title = color.xpath('.//img[@class="twisterShelf_swatch_img"]/@alt')
                    price = color.xpath('.//span[contains(@class,"a-size-mini")]/text()')
                    if img or title or price:
                        sku_items.append(
                            {
                                'img': img[0] if img else '',
                                'title': title[0] if title else '',
                                'price': price[0].strip() if price else ''
                            }
                        )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuSize(self, item):
        sku_prop = {}
        sku_size = item.xpath('//div[@id="variation_size_name"]')
        if sku_size:
            sku_prop['name'] = 'size'

            current_size = sku_size[0].xpath('.//span[@class="selection"]/text()')
            sku_items = []
            sizes = sku_size[0].xpath('./ul/li')
            if not sizes:
                select_options = item.xpath(
                    './/select[@name="dropdown_selected_size_name"]//option[@class="dropdownAvailable"]/text()')
                if select_options:
                    sku_items = [{'title': ''.join(o).strip('\n').strip()} for o in select_options]
                else:
                    sku_items.append({'title': current_size[0] if current_size else ''})
            else:
                for size in sizes:
                    itemId = size.xpath('./@data-defaultasin')
                    title = size.xpath('.//div[@class="twisterTextDiv text"]/span/text()')
                    price = size.xpath('.//span[@class="a-size-mini twisterSwatchPrice"]/text()')
                    sku_items.append(
                        {
                            'itemId': itemId[0] if itemId else '',
                            'title': title[0] if title else '',
                            'price': price[0].strip() if price else ''
                        }
                    )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuSize2(self, item):
        '''
        针对第二种页面样式的尺寸解析
        '''
        sku_prop = {}
        sku_size = item.xpath('//div[@id="shelf-size_name"]')
        if sku_size:
            sku_prop['name'] = 'size'

            current_size = sku_size[0].xpath('.//div[@id="shelf-label-size_name"]//span[@class="shelf-label-variant-name"]/text()')
            sku_items = []
            sizes = sku_size[0].xpath('./div[@id="shelfSwatchSection-size_name"]//div[@data-dp-url]')
            if not sizes:
                sku_items.append({'title': current_size[0] if current_size else ''})
            else:
                for size in sizes:
                    title = size.xpath('string(.//span[@class="a-size-base twisterShelf_swatch_text"])')
                    price = size.xpath('string(.//span[@class="a-section a-spacing-none twisterShelf_infoSection"])')
                    if title or price:
                        sku_items.append(
                            {
                                'title': title.replace('\n','').strip(),
                                'price': price.replace('\n','').strip()
                            }
                        )
            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuStyle(self, item):
        sku_prop = {}
        sku_style = item.xpath('//div[@id="variation_style_name"]')
        if sku_style:
            sku_prop['name'] = 'style'

            current_style = sku_style[0].xpath('.//span[@class="selection"]/text()')
            sku_items = []
            styles = sku_style[0].xpath('./ul/li')
            if not styles:
                sku_items.append({'title': current_style[0] if current_style else ''})
            else:
                for style in styles:
                    title = style.xpath('.//div[@class="twisterTextDiv text"]/span/text()')
                    price = style.xpath('.//div[@class="twisterSlotDiv "]/span/span/text()')
                    sku_items.append(
                        {
                            'title': title[0] if title else '',
                            'price': price[0].strip() if price else ''
                        }
                    )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuStyle2(self, item):
        '''
        针对第二种页面样式的样式解析
        '''
        sku_prop = {}
        sku_style = item.xpath('//div[@id="shelf-style_name"]')
        if sku_style:
            sku_prop['name'] = 'style'

            current_style = sku_style[0].xpath('.//div[@id="shelf-label-style_name"]//span[@class="shelf-label-variant-name"]/text()')
            sku_items = []
            styles = sku_style[0].xpath('./div[@id="shelfSwatchSection-style_name"]//div[@data-dp-url]')
            if not styles:
                sku_items.append({'title': current_style[0] if current_style else ''})
            else:
                for style in styles:
                    img = style.xpath('.//img[@class="twisterShelf_swatch_img"]/@src')
                    title = style.xpath('.//img[@class="twisterShelf_swatch_img"]/@alt')
                    price = style.xpath('string(.//span[@class="a-section a-spacing-none twisterShelf_infoSection"])')

                    if img or title or price:
                        sku_items.append(
                            {
                                'img': img[0] if img else '',
                                'title': title[0] if title else '',
                                'price': price.strip()
                            }
                        )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def getSkuFormats(self, item):
        sku_prop = {}
        sku_formats = item.xpath('//div[@id="formats"]')
        if sku_formats:
            sku_prop['name'] = 'formats'

            sku_items = []
            formats = sku_formats[0].xpath('.//ul/li')
            for format in formats:
                title = format.xpath('string(.//span[@class="a-button-inner"]/a/span[1])')
                price = format.xpath('string(.//span[@class="a-button-inner"]/a/span[2])')
                sku_items.append(
                    {
                        'title': title.strip(),
                        'price': price.strip()
                    }
                )

            sku_prop['skuItems'] = sku_items

        else:
            sku_prop = None

        return sku_prop

    def goodsComments(self, data):
        """
        商品评论清洗
        :param data:
        :return:
        """
        res = {}
        tree = etree.HTML(data)
        res_data = []
        items = tree.xpath('//div[@id="cm_cr-review_list"]/div[@data-hook="review"]')

        if not items:
            res['code'] = 201
            res['msg'] = '结果为空'
            return res

        try:
            for item in items:
                item_data = {
                    'reviewId': self.goodsCommentsFieldCleaner(item, 'reviewId'),
                    'customerName': self.goodsCommentsFieldCleaner(item, 'customerName'),
                    'customerAvatar': self.goodsCommentsFieldCleaner(item, 'customerAvatar'),
                    'customerProfile': self.goodsCommentsFieldCleaner(item, 'customerProfile'),
                    'rating': self.goodsCommentsFieldCleaner(item, 'rating'),
                    'reviewTitle': self.goodsCommentsFieldCleaner(item, 'reviewTitle'),
                    'reviewDate': self.goodsCommentsFieldCleaner(item, 'reviewDate'),
                    'reviewInfo': self.goodsCommentsFieldCleaner(item, 'reviewInfo'),
                    'reviewContent': self.goodsCommentsFieldCleaner(item, 'reviewContent'),
                }

                res_data.append(item_data)

            res['code'] = 200
            res['msg'] = 'true'
            res['data'] = res_data

        except:
            res['code'] = 401
            res['msg'] = str(traceback.format_exc())

        return res

    def goodsCommentsFieldCleaner(self, item, type):
        '''
        商品评论字段清洗
        :param item: 数据项
        :param type: 数据类型
        :return:
        '''
        item = copy.copy(item)

        result = ''
        if type == 'reviewId':
            reviewId = item.xpath('string(./@id)')
            result = reviewId.strip()

        elif type == 'customerName':
            customerName = item.xpath('string(.//span[@class="a-profile-name"])')
            result = customerName.strip()

        elif type == 'customerAvatar':
            customerAvatar = item.xpath('string(.//div[@class="a-profile-avatar"]/img/@src)')
            result = customerAvatar.strip()

        elif type == 'customerProfile':
            customerProfile = item.xpath('string(.//a[@class="a-profile"]/@href)')
            result = 'https://www.amazon.com' + customerProfile.strip()

        elif type == 'rating':
            rating = item.xpath('string(.//i[@data-hook="review-star-rating"]/span)')
            result = rating.strip()

        elif type == 'reviewTitle':
            reviewTitle = item.xpath('string(.//a[@data-hook="review-title"]/span)')
            result = reviewTitle.strip()

        elif type == 'reviewDate':
            reviewDate = item.xpath('string(.//span[@data-hook="review-date"])')
            result = reviewDate.strip()

        elif type == 'reviewInfo':
            reviewInfo = item.xpath('string(.//div[contains(@class,"review-data")])')
            result = reviewInfo.strip()

        elif type == 'reviewContent':
            reviewContent = item.xpath('string(.//span[@data-hook="review-body"])')
            result = reviewContent.strip()


        return result

    def htmlCaptchaCleaner(self,data):
        tree = etree.HTML(data)
        imgUrl_list = tree.xpath('//div[@class="a-row a-text-center"]/img/@src')
        imgUrl = imgUrl_list[0] if imgUrl_list else ''
        amzn_list = tree.xpath('//input[@name="amzn"]/@value')
        amzn = amzn_list[0] if amzn_list else ''
        amznR_list = tree.xpath('//input[@name="amzn-r"]/@value')
        amznR = amznR_list[0] if amznR_list else ''
        parmCaptcha = {
            'imgUrl':imgUrl,
            'amzn': amzn,
            'amzn-r':amznR
        }
        return parmCaptcha