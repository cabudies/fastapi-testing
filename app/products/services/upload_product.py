from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
import numpy as np
import pandas as pd

from ..dao import db_model
from ...price_list.dao import db_model as price_list_db_model
from ...variants.dao import db_model as variants_db_model
from ...products_sequence.dao import db_model as products_sequence_db_model
from ..dto import request_model
from app.web.variants.dto import request_model as variant_request_model
from app.web.manufacturer.dto import request_model as manufacturer_request_model
from app.web.brand.dto import request_model as brand_request_model
from ..repository import products_repository
from ...commons.aws_upload import upload_to_aws
from app.web.languages.repositories import language_repository
from app.web.category.repository import category_repository
from app.web.currency.repository import currency_repository
from app.web.units.repository import unit_repository
from app.web.price_list.repositories import price_list_repository
from app.web.variants.repository import variants_repository
from app.web.attributes.repositories import attributes_repository
from app.web.banned_products.repositories import banned_products_repository
from app.web.manufacturer.repository import manufacturer_repository
from app.web.brand.repository import brands_repository
from app.web.variants.services import variants_service
from app.web.attributes.services import attributes_service
from app.web.manufacturer.services import manufacturer_service
from app.web.brand.services import brands_service
from app.web.product_media.repositories import product_media_repository
from app.web.products_sequence.repository import products_sequence_repository
from app.web.attributes.dto.request_model import CreateAttribute, FeedsLanguageMapping, UpdateAttributes
from app.web.attributes.dao import db_model as attributes_db_model
from app.web.product_media.repositories import product_media_repository
from ...commons import enums, misc, mailclient
from ..services import products_service


class UploadProduct():

    def __init__(self, data, session: AsyncSession):
        self.data = data
        self.session = session
        self.unique_categories_list_details = []
        self.unique_unit_codes_list_details = []
        self.unique_country_of_origin_list_details = []
        self.unique_language_codes_list_details = []
        self.unique_manufacturer_list_details = []
        self.unique_brand_list_details = []
        self.MANDATORY_COLUMNS = [
            "product_name", "sku", "language_code", "sub_category", "category",
            "unit_value", "unit_code", "country_of_origin"
        ]


    async def validate_csv_format(
        self, data: pd.DataFrame, columns: List[str]
    ):
        if all(item in columns for item in self.MANDATORY_COLUMNS) == False:
            raise HTTPException(
                status_code=400,
                detail="{} columns are mandatory.".format(", ".join(self.MANDATORY_COLUMNS))
            )
        
        if data['sku'].duplicated().any():
            raise HTTPException(
                status_code=400,
                detail="Duplicate value in sku is not allowed."
            )
        
        null_values_check = data[self.MANDATORY_COLUMNS].isna().any().to_dict()
        for key, value in null_values_check.items():
            if value == True:
                raise HTTPException(
                    status_code=400,
                    detail="Null values in {} column.".format(key)
                )

        
    def map_all_columns_data_to_dataframe_for_category(self, value):
        category_id = list(
            filter(
                lambda x: x.name == value, 
                self.unique_categories_list_details
            )
        )
        if len(category_id) == 1:
            return category_id[0].category_id
        return None


    def map_all_columns_data_to_dataframe_for_parent_category(self, value):
        category_id = list(
            filter(
                lambda x: x.name == value, 
                self.unique_categories_list_details
            )
        )
        if len(category_id) == 1:
            return category_id[0].category_id
        return None


    def map_all_columns_data_to_dataframe_for_unit(self, value):
        unit_id = list(
            filter(
                lambda x: x.unit_code == value, 
                self.unique_unit_codes_list_details
            )
        )
        if len(unit_id) == 1:
            return unit_id[0].id
        return None


    def map_all_columns_data_to_dataframe_for_language(self, value):
        if self.unique_language_codes_list_details.language_code == value:
            return self.unique_language_codes_list_details.id
        else:
            return 2


    def map_all_columns_data_to_dataframe_for_country(self, value):
        country_id = list(
            filter(
                lambda x: x.language_code == value, 
                self.unique_country_of_origin_list_details
            )
        )
        return country_id[0].id


    def map_all_columns_data_to_dataframe_for_manufacturer(self, value):
        if value == 'None':
            return None

        for manufacturer in self.unique_manufacturer_list_details:
            if manufacturer != 'None':
                if manufacturer.name.lower() == value.lower():
                    return manufacturer.manufacturer_id
        
        return None


    def map_all_columns_data_to_dataframe_for_brand(self, value):
        if value == 'None':
            return None
        
        for brand in self.unique_brand_list_details:
            if brand != 'None':
                if brand.name.lower() == value.lower():
                    return brand.brand_id
        
        return None


    async def process_products_data(self):
        columns = list(
            map(
                lambda x: x.lower(), 
                self.data.columns.to_list()
            )
        )
        self.data.columns = columns
        
        await self.validate_csv_format(data=self.data, columns=self.data.columns)

        self.data['language_code'] = self.data['language_code'].map(lambda x: x.lower())
        self.data['unit_code'] = self.data['unit_code'].map(lambda x: x.lower())
        self.data['country_of_origin'] = self.data['country_of_origin'].map(lambda x: x.lower())
        self.data['package_type'] = self.data['package_type'].map(lambda x: x.lower())

        self.data['description'].fillna('', inplace=True)
        self.data['manufacturer'].fillna('None', inplace=True)
        self.data['brand'].fillna('None', inplace=True)

        unique_language_codes_list = self.data['language_code'].unique().tolist()
        unique_categories_list = self.data['sub_category'].unique().tolist()
        unique_attribute_type_list = self.data['category'].unique().tolist()
        unique_manufacturer_list = self.data['manufacturer'].unique().tolist()
        unique_brand_list = self.data['brand'].unique().tolist()
        unique_unit_codes_list = self.data['unit_code'].unique().tolist()
        
        ######## checking for unique language #############
        if len(unique_language_codes_list)>1:
            raise HTTPException(
                status_code=400,
                detail="Specify self.data for only 1 language at a time."
            )

        self.unique_language_codes_list_details = await language_repository.get_language_by_language_code(
            session=self.session, language_code=unique_language_codes_list[0]
        )
        
        if self.unique_language_codes_list_details is None:
            raise HTTPException(
                status_code=400,
                detail="Specified language code does not exists in our self.database."
            )
        
        self.data['language_id'] = self.unique_language_codes_list_details.id

        ############# checking for attributes #################
        AVAILABLE_ATTRIBUTES_TYPE = [e.value for e in enums.AttributeTypeEnum]
        if len(unique_attribute_type_list) != 1:
            raise HTTPException(
                status_code=400,
                detail="Only 1 categories self.data is allowed to be uploaded at a time."
            )
        if unique_attribute_type_list[0].lower() not in AVAILABLE_ATTRIBUTES_TYPE:
            raise HTTPException(
                status_code=400,
                detail="Specified category does not exists in our self.database."
            )
        
        if enums.AttributeTypeEnum.agri_machinery.value == unique_attribute_type_list[0].lower():
            attribute_type = "machinery"
        elif enums.AttributeTypeEnum.agro_chemicals.value == unique_attribute_type_list[0].lower():
            attribute_type = "chemicals"
        else:
            attribute_type = unique_attribute_type_list[0].lower()
        
        ################ checking for sub categories ###################
        self.unique_categories_list_details = await category_repository.get_category_list_by_language_name(
            session=self.session, name_list=unique_categories_list, 
            language_id=self.unique_language_codes_list_details.id
        )
        
        if len(self.unique_categories_list_details) != len(unique_categories_list):
            raise HTTPException(
                status_code=400,
                detail="Some of the defined categories are not available"
            )
        self.data['sub_category_id'] = self.data['sub_category'].apply(self.map_all_columns_data_to_dataframe_for_category)

        parent_categories_with_ids = await category_repository.get_parent_category_list_by_category_ids_list(
            session=self.session, category_ids_list=self.data['sub_category_id']
        )
        parent_categories_with_ids = set(parent_categories_with_ids)
        if len(parent_categories_with_ids) == 0:
            parent_categories_with_ids = set(self.data['sub_category_id'].unique().tolist())
        
        parent_categories_with_ids = tuple(parent_categories_with_ids)

        ########## checking unit details ##############
        self.unique_unit_codes_list_details = await unit_repository.get_units_list_by_unit_code_list(
            session=self.session, unit_code_list=unique_unit_codes_list
        )
        if len(self.unique_unit_codes_list_details) != len(unique_unit_codes_list):
            raise HTTPException(
                status_code=400,
                detail="Some of the defined units are not available"
            )
        self.data['unit_id'] = self.data['unit_code'].apply(self.map_all_columns_data_to_dataframe_for_unit)

        ################## checking manufacturer id against manufacturer name ########3
        self.unique_manufacturer_list_details = []
        
        for name in unique_manufacturer_list:
            if name == 'None':
                self.unique_manufacturer_list_details.append('None')
                continue
            manufacturer_details = await manufacturer_repository.get_manufacturer_details_by_manufacturer_name_and_type_like(
                session=self.session, manufacturer_name=name
            )
            if manufacturer_details is not None:
                self.unique_manufacturer_list_details.append(manufacturer_details)
            else:
                new_manufacturer_model = manufacturer_request_model.ManufacturerDto(
                    data = [
                        manufacturer_request_model.ManufacturerLanguageMappingDto(
                            name = name,
                            language_id = 2
                        )
                    ],
                    type = [parent_categories_with_ids[0]]
                )
                create_new_manufacturer = await manufacturer_service.create_manufacturer_via_product_import(
                    session=self.session, manufacturer_obj=new_manufacturer_model
                )
                self.unique_manufacturer_list_details.append(create_new_manufacturer)

        if len(self.unique_manufacturer_list_details) != len(unique_manufacturer_list):
            raise HTTPException(
                status_code=400,
                detail="Some of the defined manufacturer are not available"
            )
        
        if len(self.unique_manufacturer_list_details) > 0: 
            self.data['manufacturer_id'] = self.data['manufacturer'].apply(self.map_all_columns_data_to_dataframe_for_manufacturer)
        else:
            self.data['manufacturer_id'] = np.nan
        
        ############## checking brand id with brand name ############
        for name in unique_brand_list:
            if name == 'None':
                self.unique_brand_list_details.append('None')
                continue
            brand_details = await brands_repository.get_brand_details_by_brand_name_and_type_like(
                session=self.session, brand_name=name
            )
            if brand_details is not None:
                self.unique_brand_list_details.append(brand_details)
            else:
                manufacturer_id = self.data[self.data['brand'] == name]['manufacturer_id']
                
                new_brand_model = brand_request_model.BrandDto(
                    data = [
                        brand_request_model.BrandLanguageMappingDto(
                            name = name,
                            language_id = 2
                        )
                    ],
                    manufacturer_id = int(manufacturer_id.to_list()[0]),
                    type = unique_attribute_type_list[0].lower()
                )
                create_new_brand = await brands_service.create_brand_via_product_import(
                    session=self.session, brand_obj=new_brand_model
                )

                self.unique_brand_list_details.append(create_new_brand)

        if len(self.unique_brand_list_details) != len(unique_brand_list):
            raise HTTPException(
                status_code=400,
                detail="Some of the defined brands are not available"
            )

        if len(self.unique_brand_list_details) > 0: 
            self.data['brand_id'] = self.data['brand'].apply(self.map_all_columns_data_to_dataframe_for_brand)
        else:
            self.data['brand_id'] = np.nan
        
        already_created_product = []
        created_product_name_list = []
        updated_product_name_list = []

        created_variant_sku_list = []
        updated_variant_sku_list = []

        ####### start creating products and variants ##############
        for index, row in self.data.iterrows():
            # continue
            product_id = None
            create_attribute_model = None
            update_attribute_model = None

            #### check if any product with same name already exists ########
            product_already_exists = list(
                filter(
                    lambda x: x['name']==row.product_name, 
                    already_created_product
                )
            )
            
            if len(product_already_exists) == 1:
                product_id = product_already_exists[0]['id']

            language_data = [
                {
                    "name": row.product_name,
                    "description": row.description, 
                    "language_id": row.language_id
                }
            ]

            ##### search if product exists ##########
            if product_id is None:
                product_names_list = await products_repository.get_product_by_name_like_and_language_id(
                    session=self.session,
                    name=row.product_name,
                    name_condition=enums.NameCondition.eq,
                    language_id=self.unique_language_codes_list_details.id,
                    is_active=None
                )
                
                if len(product_names_list)>0:
                    product_id = product_names_list[0][0]

                    product_update_request_model = request_model.UpdateProduct(
                        id = product_id,
                        data = str(language_data),
                        category_id = row.sub_category_id,
                        currency_id = 1,
                        manufacturer_id = None if pd.isna(row.manufacturer_id) else row.manufacturer_id,
                        brand_id = None if pd.isna(row.brand_id) else row.brand_id,
                        sold_by = 'Faarms Pvt. Ltd.' if pd.isna(row.sold_by) else row.sold_by,
                        image = None,
                        is_active = False if pd.isna(row.product_is_active) else row.product_is_active
                    )

                    await products_service.update_product_via_product_import(
                        session=self.session, product_update_model=product_update_request_model, 
                        image=None, attributes={},
                        product_id=product_id
                    )
                    
                    updated_product_name_list.append({
                        'name': row.product_name,
                        'id': product_id
                    })
                
                else:
                    ######## create product #########
                    
                    new_product_model = request_model.CreateProducts(
                        data = str(language_data),
                        category_id = row.sub_category_id,
                        currency_id = 1,
                        manufacturer_id = None if pd.isna(row.manufacturer_id) else row.manufacturer_id,
                        brand_id = None if pd.isna(row.brand_id) else row.brand_id,
                        sold_by = 'Faarms Pvt. Ltd.' if pd.isna(row.sold_by) else row.sold_by,
                        image = None
                    )

                    create_new_product = await products_service.create_product_via_product_import(
                        session=self.session, product_obj=new_product_model, image=None,
                        attributes={}
                    )
                    
                    product_id = create_new_product[0].id
                    created_product_name_list.append({
                        'name': row.product_name,
                        'id': product_id
                    })  
            
            else:
                already_created_product.append({
                    'name': row.product_name,
                    'id': product_id
                })
            
            ####### search variant ###############
            get_variant_details_if_variant_already_exists = await variants_repository.get_variants_by_sku(
                session=self.session, sku=row.sku
            )
                
            create_attribute_model = CreateAttribute(
                package_type = 'bag' if pd.isna(row.package_type) else row.package_type,
                # manufacturer_id = None if pd.isna(row.manufacturer_id) else row.manufacturer_id,
                # brand_id = row.brand_id,
                # sold_by = 'Faarms' if pd.isna(row.sold_by) else row.sold_by,
                best_before_days = 0 if pd.isna(row.best_before_days) else row.best_before_days,
                product_category = row.sub_category_id,
                language_id = row.language_id,
                country_of_origin = 1, ## static country of origin
                attribute_type = row.category.lower(),
            )

            update_attribute_model = UpdateAttributes(
                package_type = 'bag' if pd.isna(row.package_type) else row.package_type,
                # manufacturer_id = None if pd.isna(row.manufacturer_id) else row.manufacturer_id,
                # brand_id = row.brand_id,
                # sold_by = 'Faarms' if pd.isna(row.sold_by) else row.sold_by,
                best_before_days = 0 if pd.isna(row.best_before_days) else row.best_before_days,
                product_category = row.sub_category_id,
                language_id = row.language_id,
                country_of_origin = 1, ## static country of origin
                attribute_type = row.category.lower()
            )

            if row.category.lower() == enums.AttributeTypeEnum.feeds:

                setattr(create_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(create_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(create_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(create_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(create_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(create_attribute_model, "livestock_type", None if pd.isna(row.livestock_type) else row.livestock_type)

                setattr(update_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(update_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(update_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(update_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(update_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(update_attribute_model, "livestock_type", None if pd.isna(row.livestock_type) else row.livestock_type)

            elif row.category.lower() == enums.AttributeTypeEnum.seeds:
                
                setattr(create_attribute_model, "first_harvest", None if pd.isna(row.first_harvest) else row.first_harvest)
                setattr(create_attribute_model, "sowing_season", None if pd.isna(row.sowing_season) else row.sowing_season)
                setattr(create_attribute_model, "locality_for_sowing", None if pd.isna(row.locality_for_sowing) else row.locality_for_sowing)
                setattr(create_attribute_model, "method_of_growing", None if pd.isna(row.method_of_growing) else row.method_of_growing)
                setattr(create_attribute_model, "holder_type", None if pd.isna(row.holder_type) else row.holder_type)
                setattr(create_attribute_model, "duration_of_variety", None if pd.isna(row.duration_of_variety) else row.duration_of_variety)
                setattr(create_attribute_model, "additional_description", None if pd.isna(row.additional_description) else row.additional_description)
                setattr(create_attribute_model, "dose", 0 if pd.isna(row.dose) else row.dose)

                setattr(update_attribute_model, "first_harvest", None if pd.isna(row.first_harvest) else row.first_harvest)
                setattr(update_attribute_model, "sowing_season", None if pd.isna(row.sowing_season) else row.sowing_season)
                setattr(update_attribute_model, "locality_for_sowing", None if pd.isna(row.locality_for_sowing) else row.locality_for_sowing)
                setattr(update_attribute_model, "method_of_growing", None if pd.isna(row.method_of_growing) else row.method_of_growing)
                setattr(update_attribute_model, "holder_type", None if pd.isna(row.holder_type) else row.holder_type)
                setattr(update_attribute_model, "duration_of_variety", None if pd.isna(row.duration_of_variety) else row.duration_of_variety)
                setattr(update_attribute_model, "additional_description", None if pd.isna(row.additional_description) else row.additional_description)
                setattr(update_attribute_model, "dose", 0 if pd.isna(row.dose) else row.dose)
                
            elif (
                (row.category.lower() == enums.AttributeTypeEnum.chemicals) 
                or 
                (row.category.lower() == enums.AttributeTypeEnum.agro_chemicals.value)
            ):
                
                setattr(create_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(create_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(create_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(create_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(create_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(create_attribute_model, "target_pests", None if pd.isna(row.target_pests) else row.target_pests)

                setattr(update_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(update_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(update_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(update_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(update_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(update_attribute_model, "target_pests", None if pd.isna(row.target_pests) else row.target_pests)

            elif row.category.lower() == enums.AttributeTypeEnum.fertilizers:
                
                setattr(create_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(create_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(create_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(create_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(create_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(create_attribute_model, "target_pests", None if pd.isna(row.target_pests) else row.target_pests)

                setattr(update_attribute_model, "min_order_qty", 0 if pd.isna(row.min_order_qty) else row.min_order_qty)
                setattr(update_attribute_model, "max_order_qty", 0 if pd.isna(row.max_order_qty) else row.max_order_qty)
                setattr(update_attribute_model, "ingredients", None if pd.isna(row.ingredients) else row.ingredients)
                setattr(update_attribute_model, "formulations", None if pd.isna(row.formulations) else row.formulations)
                setattr(update_attribute_model, "how_to_use", None if pd.isna(row.how_to_use) else row.how_to_use)
                setattr(update_attribute_model, "target_pests", None if pd.isna(row.target_pests) else row.target_pests)

            elif (
                (row.category.lower() == enums.AttributeTypeEnum.machinery) 
                or 
                (row.category.lower() == enums.AttributeTypeEnum.agri_machinery.value)
            ):
                
                setattr(create_attribute_model, "product_weight", 0 if pd.isna(row.product_weight) else row.product_weight)
                setattr(create_attribute_model, "motor_power", 0 if pd.isna(row.motor_power) else row.motor_power)
                setattr(create_attribute_model, "product_type", None if pd.isna(row.product_type) else row.product_type)
                setattr(create_attribute_model, "purpose", None if pd.isna(row.purpose) else row.purpose)

                setattr(update_attribute_model, "product_weight", 0 if pd.isna(row.product_weight) else row.product_weight)
                setattr(update_attribute_model, "motor_power", 0 if pd.isna(row.motor_power) else row.motor_power)
                setattr(update_attribute_model, "product_type", None if pd.isna(row.product_type) else row.product_type)
                setattr(update_attribute_model, "purpose", None if pd.isna(row.purpose) else row.purpose)

            if (
                (create_attribute_model == None) 
                or 
                (update_attribute_model == None)
            ):
                raise HTTPException(
                    status_code=400,
                    detail="No attribute details to be created or updated for product name - {}".format(row.product_name)
                )
            
            ############### create variant ###################
            if len(get_variant_details_if_variant_already_exists) == 0:
                new_variant_model = variant_request_model.CreateVariant(
                    sku = row.sku,
                    product_id = product_id,
                    category_id = row.sub_category_id,
                    unit_type_id = row.unit_id,
                    unit_multiples = row.unit_value,
                    attribute_type = attribute_type,
                    is_default = True,
                    is_inventory_check_required = row.is_inventory_check_required,
                    attributes = [create_attribute_model]
                )
                
                await variants_service.create_variant_via_product_import(
                    session=self.session, variant_obj=new_variant_model, 
                    attributes={}
                )
                
                created_variant_sku_list.append(row.sku)
            
            else:
                ############### update variant ###################
                update_variant_model = variant_request_model.UpdateVariant(
                    # sku = row.sku,
                    product_id = product_id,
                    id = get_variant_details_if_variant_already_exists[0].id,
                    category_id = row.sub_category_id,
                    unit_type_id = row.unit_id,
                    unit_multiples = row.unit_value,
                    attribute_type = attribute_type,
                    is_default = True,
                    attributes = [update_attribute_model],
                    is_inventory_check_required = row.is_inventory_check_required,
                    is_active = True if pd.isna(row.sku_is_active) else row.sku_is_active
                )
                
                await variants_service.update_variant_via_product_import(
                    session=self.session, id=get_variant_details_if_variant_already_exists[0].id, 
                    variant_obj=update_variant_model, attributes={}
                )

                updated_variant_sku_list.append(row.sku)

        status = {
            'total_products_in_csv': self.data.shape[0],
            'created_product_name_count': len(created_product_name_list),
            'created_variant_sku_count': len(created_variant_sku_list),
            'updated_product_name_count': len(updated_product_name_list),
            'updated_variant_sku_count': len(updated_variant_sku_list),

            'created_product_name_list': created_product_name_list,
            'created_variant_sku_list': created_variant_sku_list,
            'updated_product_name_list': updated_product_name_list,
            'updated_variant_sku_list': updated_variant_sku_list
        }
        
        return status


