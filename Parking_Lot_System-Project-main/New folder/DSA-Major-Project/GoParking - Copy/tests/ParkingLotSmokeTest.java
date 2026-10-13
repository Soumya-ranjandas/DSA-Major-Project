public class ParkingLotSmokeTest {

    public static void main(String[] args) {
        ParkingLot lot = new ParkingLot(2);

        String first = lot.parkVehicle(
            new Vehicle("ab-123", "Blue", "Sedan"));
        require(first.equals("OK|Vehicle parked|AB-123|Blue|Sedan|1"),
            "The first vehicle should receive the lowest slot.");

        String second = lot.parkVehicle(
            new Vehicle("cd-456", "Green", "Motorcycle"));
        require(second.endsWith("|2"),
            "The second vehicle should receive the next slot.");

        String full = lot.parkVehicle(
            new Vehicle("ef-789", "Red", "Bicycle"));
        require(full.equals("ERROR|Parking lot is full"),
            "A full lot should reject additional vehicles.");

        String invalid = lot.parkVehicle(
            new Vehicle("ef-789", "Red", "Unlisted vehicle"));
        require(invalid.equals("ERROR|Invalid vehicle details"),
            "Unsupported vehicle categories should be rejected.");

        String removed = lot.removeVehicle("ab-123");
        require(removed.equals("OK|Vehicle removed|AB-123|1"),
            "Removing a vehicle should report its released slot.");

        String third = lot.parkVehicle(
            new Vehicle("ef-789", "Red", "Bicycle"));
        require(third.endsWith("|1"),
            "The lowest released slot should be allocated next.");

        String found = lot.findVehicle("EF-789");
        require(found.equals("FOUND|EF-789|Red|Bicycle|1"),
            "Registration lookup should be case-insensitive.");

        System.out.println("ParkingLot smoke tests passed.");
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
