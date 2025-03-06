import numpy as np
import pickle
import logging

# 🚀 Logger setup
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Load the trained model and preprocessing tools
xgb_model = pickle.load(open("MODEL/xgboost.pkl", "rb"))
scaler = pickle.load(open("MODEL/scaler.pkl", "rb"))
crop_encoder = pickle.load(open("MODEL/crop_encoder.pkl", "rb"))
region_encoder = pickle.load(open("MODEL/region_encoder.pkl", "rb"))

# Available crop and region names
available_crops = list(crop_encoder.classes_)
available_regions = list(region_encoder.classes_)


# ✅ Function to get user input
def get_user_input():
    while True:
        crop_choice = input("\nEnter Crop Name: ").strip().capitalize()
        region_choice = input("Enter Region Name: ").strip().capitalize()

        if crop_choice not in available_crops:
            print(
                f"❌ Invalid crop: {crop_choice}. Please enter a valid crop name."
            )
            continue

        if region_choice not in available_regions:
            print(
                f"❌ Invalid region: {region_choice}. Please enter a valid region name."
            )
            continue

        crop_index = available_crops.index(crop_choice)
        region_index = available_regions.index(region_choice)

        user_numerical_input = [
            float(input("Enter Soil pH: ")),
            int(input("Enter Nitrogen content: ")),
            int(input("Enter Phosphorus content: ")),
            int(input("Enter Potassium content: ")),
            float(input("Enter Temperature (°C): ")),
            float(input("Enter Humidity (%): ")),
            float(input("Enter Rainfall (mm): "))
        ]

        # ✅ Calculate New Features
        soil_quality_index = (user_numerical_input[0] *
                              user_numerical_input[1]) / 10
        temp_humidity_ratio = user_numerical_input[4] / (
            user_numerical_input[5] + 1)  # Avoid division by zero
        rainfall_nutrient_ratio = user_numerical_input[6] / (
            user_numerical_input[1] + user_numerical_input[2] +
            user_numerical_input[3] + 1)

        # Combine features into an input array
        full_input = user_numerical_input + [
            crop_index, region_index, soil_quality_index, temp_humidity_ratio,
            rainfall_nutrient_ratio
        ]

        return np.array(full_input), crop_choice


# ✅ Function to predict crop yield and suggest alternatives
def predict_crop_yield(user_input, crop_name):
    user_scaled = scaler.transform(user_input.reshape(1, -1))
    predicted_yield = xgb_model.predict(user_scaled)[0]

    # Convert yield into percentage (assuming max possible yield is 10 tons/ha for scaling)
    yield_percentage = (predicted_yield / 10) * 100

    print(
        f"\n✅ The crop '{crop_name}' is expected to yield **{predicted_yield:.2f} tons per hectare ({yield_percentage:.2f}% probability).**"
    )

    if yield_percentage < 40:
        print(
            f"\n⚠️ The chances of '{crop_name}' yielding are **low ({yield_percentage:.2f}%)**."
        )
        alternative_crop = suggest_alternative_crop(user_input)
        print(
            f"👉 Consider growing **'{alternative_crop}'** instead for better yield!"
        )

    return predicted_yield


# ✅ Function to suggest an alternative crop
def suggest_alternative_crop(user_input):
    best_yield = 0
    best_crop = None

    for crop in available_crops:
        crop_index = available_crops.index(crop)
        modified_input = user_input.copy()
        modified_input[-3] = crop_index  # Change only the crop index

        crop_scaled = scaler.transform(modified_input.reshape(1, -1))
        predicted_yield = xgb_model.predict(crop_scaled)[0]

        if predicted_yield > best_yield:
            best_yield = predicted_yield
            best_crop = crop

    return best_crop


# ✅ Run the Prediction Loop
def test_model():
    while True:
        try:
            user_input, crop_name = get_user_input()
            print("\n🔄 Processing input and making a prediction...")
            predict_crop_yield(user_input, crop_name)

            retry = input("Would you like to check another crop? (yes/no): "
                        ).strip().lower()
            if retry != "yes":
                print(
                    "\nThank you for using the Crop Yield Prediction System! 🌾"
                )
                break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Error during prediction: {e}")


# Start the Model
test_model()
