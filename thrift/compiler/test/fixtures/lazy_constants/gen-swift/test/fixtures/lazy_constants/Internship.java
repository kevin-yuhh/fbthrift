package test.fixtures.lazy_constants;

import com.facebook.swift.codec.*;
import com.facebook.swift.codec.ThriftField.Requiredness;
import com.facebook.swift.codec.ThriftField.Recursiveness;
import java.util.*;

import static com.google.common.base.MoreObjects.toStringHelper;

@ThriftStruct("Internship")
public final class Internship
{
    @ThriftConstructor
    public Internship(
        @ThriftField(value=1, name="weeks", requiredness=Requiredness.REQUIRED) final int weeks,
        @ThriftField(value=2, name="title", requiredness=Requiredness.NONE) final String title,
        @ThriftField(value=3, name="employer", requiredness=Requiredness.OPTIONAL) final test.fixtures.lazy_constants.Company employer
    ) {
        this.weeks = weeks;
        this.title = title;
        this.employer = employer;
    }

    public static class Builder {
        private int weeks;

        public Builder setWeeks(int weeks) {
            this.weeks = weeks;
            return this;
        }
        private String title;

        public Builder setTitle(String title) {
            this.title = title;
            return this;
        }
        private test.fixtures.lazy_constants.Company employer;

        public Builder setEmployer(test.fixtures.lazy_constants.Company employer) {
            this.employer = employer;
            return this;
        }

        public Builder() { }
        public Builder(Internship other) {
            this.weeks = other.weeks;
            this.title = other.title;
            this.employer = other.employer;
        }

        public Internship build() {
            return new Internship (
                this.weeks,
                this.title,
                this.employer
            );
        }
    }

    private final int weeks;

    @ThriftField(value=1, name="weeks", requiredness=Requiredness.REQUIRED)
    public int getWeeks() { return weeks; }

    private final String title;

    @ThriftField(value=2, name="title", requiredness=Requiredness.NONE)
    public String getTitle() { return title; }

    private final test.fixtures.lazy_constants.Company employer;

    @ThriftField(value=3, name="employer", requiredness=Requiredness.OPTIONAL)
    public test.fixtures.lazy_constants.Company getEmployer() { return employer; }

    @Override
    public String toString()
    {
        return toStringHelper(this)
            .add("weeks", weeks)
            .add("title", title)
            .add("employer", employer)
            .toString();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }

        Internship other = (Internship)o;

        return
            Objects.equals(weeks, other.weeks) &&
            Objects.equals(title, other.title) &&
            Objects.equals(employer, other.employer);
    }

    @Override
    public int hashCode() {
        return Arrays.deepHashCode(new Object[] {
            weeks,
            title,
            employer
        });
    }
}